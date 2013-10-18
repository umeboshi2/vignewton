import csv
import re
from datetime import datetime, timedelta

import requests
import transaction
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import or_

from vignewton.models.main import Account, AccountBalance
from vignewton.models.main import UserAccount

from vignewton.models.main import BaseTransfer, Transaction
from vignewton.models.main import TransactionType


from vignewton.managers.base import InsufficientFundsError
from vignewton.managers.base import AmountTooHighError
from vignewton.managers.base import NoBetsManagerError
from vignewton.managers.util import determine_max_bet

# win and loss are referenced from viewpoint of user
#
# There are four predefined accounts:
# -----------------------------------
# Cash_Account - This is the available money that
# is owned by the system.
#
# Wagers_Account - This is the money that is currently
# being wagered.  On a win, the money goes back into
# the user's account.  On a loss, the money goes to the
# cash account.
#
# JuiceInsurance_Account - This is the money that is being
# held to cover the juice fee on a loss.  When a loss occurs
# an appropriate amount of money goes to cash account.  On
# a win, an appropriate amount goes to the user account.
#
# InTheWild_Account - This is the money that is in the wild.
# This account should always be negative and be equal to all
# the money held captive in the system.  This account exists
# to keep the books well balanced.
#
#
#
#
#

def mkdbl_entries(txn, creditor, debtor, amount, now):
    c = BaseTransfer()
    c.txn_id = txn.id
    c.created = now
    c.account_id = creditor
    c.amount = amount
    d = BaseTransfer()
    d.txn_id = txn.id
    d.created = now
    d.account_id = debtor
    d.amount = -amount
    return c, d

class AccountingManager(object):
    def __init__(self, session):
        self.session = session
        self.db_account = Account
        self.db_transfer = BaseTransfer
        self.db_account_bal = AccountBalance
        self.db_bal = self.db_account_bal
            
        self.bets = None
        self._refresh_standard_accounts()

    def refresh(self):
        self._refresh_standard_accounts()
        
    def _refresh_standard_accounts(self):
        try:
            self.cash = self._get_cash_account()
        except NoResultFound:
            self.cash = None
        try:
            self.wagers = self._get_wagers_account()
        except NoResultFound:
            self.wagers = None
        try:
            self.juice = self._get_juice_account()
        except NoResultFound:
            self.juice = None
        try:
            self.inthewild = self._get_wild_account()
        except NoResultFound:
            self.inthewild = None
        
    def initialize_bets_manager(self):
        from vignewton.managers.bets import BetsManager
        self.bets = BetsManager(self.session)
        
    def _get_cash_account(self):
        q = self.session.query(Account)
        q = q.filter_by(name='Cash_Account')
        return q.one()
    
    def _get_wagers_account(self):
        q = self.session.query(Account)
        q = q.filter_by(name='Wagers_Account')
        return q.one()
    
    def _get_juice_account(self):
        q = self.session.query(Account)
        q = q.filter_by(name='JuiceInsurance_Account')
        return q.one()
    
    def _get_wild_account(self):
        q = self.session.query(Account)
        q = q.filter_by(name='InTheWild_Account')
        return q.one()
    
    def _get_txn_type(self, name):
        q = self.session.query(TransactionType)
        q = q.filter_by(name=name)
        return q.one()
    
    def add_account(self, name):
        with transaction.manager:
            acct = Account()
            acct.name = name
            self.session.add(acct)
            acct = self.session.merge(acct)
            bal = AccountBalance()
            bal.account_id = acct.id
            bal.balance = 0
            self.session.add(bal)
        return self.session.merge(acct)

    def add_user_account(self, user, name=None):
        if name is None:
            name = user.username
        acct = self.add_account(name)
        with transaction.manager:
            ua = UserAccount()
            ua.account_id = acct.id
            ua.user_id = user.id
            self.session.add(ua)
        return self.session.merge(ua)

    def get(self, user_id):
        q = self.session.query(UserAccount)
        q = q.filter_by(user_id=user_id)
        return q.one().account

    def user_account_query(self):
        return self.session.query(UserAccount)
        
    
    def get_balance(self, account_id):
        q = self.session.query(AccountBalance)
        return q.get(account_id)

    def _std_acct_ids(self):
        cash_id = self.cash.id
        wild_id = self.inthewild.id
        wagers_id = self.wagers.id
        juice_id = self.juice.id
        return [cash_id, wild_id, wagers_id, juice_id]
        
    def get_account_balance_total(self):
        standard_accounts = self._std_acct_ids()
        q = self.session.query(func.sum(AccountBalance.balance))
        # where account_id not in standard_accounts
        q = q.filter(~AccountBalance.account_id.in_(standard_accounts))
        return q.one()

    def get_user_accounts(self):
        standard_accounts = self._std_acct_ids()
        q = self.session.query(Account)
        q = q.filter(~Account.id.in_(standard_accounts))
        return q.all()
    
    # This comes from the wild
    def add_to_cash(self, amount):
        if amount <= 0:
            raise InsufficientFundsError, 'bad amount %d' % amount
        with transaction.manager:
            cash = self.get_balance(self.cash.id)
            wild = self.get_balance(self.inthewild.id)
            now = datetime.now()
            ttype = self._get_txn_type('deposit_cash')
            txn = Transaction()
            txn.type_id = ttype.id
            txn.created = now
            self.session.add(txn)
            txn = self.session.merge(txn)
            # transfer to cash and from wild
            to_cash, from_wild = mkdbl_entries(txn,
                                               self.cash.id,
                                               self.inthewild.id,
                                               amount,
                                               now)
            #adjust balances
            cash.balance += amount
            wild.balance -= amount
            # update database
            self.session.add(to_cash)
            self.session.add(from_wild)
            cash = self.session.merge(cash)
            wild = self.session.merge(wild)
        self._refresh_standard_accounts()
        return self.session.merge(txn)

    def take_from_cash(self, amount):
        cash_balance = self.get_balance(self.cash.id).balance
        if cash_balance < amount:
            msg = "Cash balance %d, amount %d" % (cash_balance, amount)
            raise InsufficientFundsError, msg
        with transaction.manager:
            now = datetime.now()
            ttype = self._get_txn_type('withdraw_cash')
            txn = Transaction()
            txn.type_id = ttype.id
            txn.created = now
            self.session.add(txn)
            txn = self.session.merge(txn)
            cash = self.get_balance(self.cash.id)
            wild = self.get_balance(self.inthewild.id)
            # transfer to wild and from cash
            to_wild, from_cash = mkdbl_entries(txn,
                                               self.inthewild.id,
                                               self.cash.id,
                                               amount,
                                               now)
            #adjust balances
            wild.balance += amount
            cash.balance -= amount
            # update database
            self.session.add(to_wild)
            self.session.add(from_cash)
            cash = self.session.merge(cash)
            wild = self.session.merge(wild)
        self._refresh_standard_accounts()
        return self.session.merge(txn)

       
        
        

    def deposit_to_account(self, account_id, amount):
        if amount <= 0:
            raise InsufficientFundsError, 'bad amount %d' % amount
        with transaction.manager:
            acct = self.get_balance(account_id)
            wild = self.get_balance(self.inthewild.id)
            now = datetime.now()
            ttype = self._get_txn_type('deposit_acct')
            txn = Transaction()
            txn.type_id = ttype.id
            txn.created = now
            self.session.add(txn)
            txn = self.session.merge(txn)
            # make double entries
            to_acct, from_wild = mkdbl_entries(txn,
                                               account_id,
                                               self.inthewild.id,
                                               amount,
                                               now)
            #adjust balances
            acct.balance += amount
            wild.balance -= amount
            # update database
            self.session.add(to_acct)
            self.session.add(from_wild)
            acct = self.session.merge(acct)
            wild = self.session.merge(wild)
        self._refresh_standard_accounts()
        return self.session.merge(txn)

    def pay_account(self, account_id, amount):
        "from user account to wild"
        balance = self.get_balance(account_id)
        if amount > balance.balance:
            msg = "Amount %d, current balance %d" % (amount, balance.balance)
            raise InsufficientFundsError, msg
        with transaction.manager:
            acct = self.get_balance(account_id)
            wild = self.get_balance(self.inthewild.id)
            now = datetime.now()
            ttype = self._get_txn_type('withdraw_acct')
            txn = Transaction()
            txn.type_id = ttype.id
            txn.created = now
            self.session.add(txn)
            txn = self.session.merge(txn)
            # transfer to wild
            # transfer from account
            to_wild, from_acct = mkdbl_entries(txn,
                                               self.inthewild.id,
                                               account_id,
                                               amount,
                                               now)
            
            #adjust balances
            wild.balance += amount
            acct.balance -= amount
            # update database
            self.session.add(to_wild)
            self.session.add(from_acct)
            acct = self.session.merge(acct)
            wild = self.session.merge(wild)
        self._refresh_standard_accounts()
        return self.session.merge(txn)


    # This just moves money from the
    # user account to the wager and juice
    # accounts.  The amount of the bet
    # is permanently stored on the user bets table.
    # A matching amount is moved from the cash accout
    # to the wager account to cover the bet.
    def place_bet(self, account_id, amount):
        juice_insurance = amount / 10
        total = amount + juice_insurance
        acct = self.get_balance(account_id)
        cash = self.get_balance(self.cash.id)
        if total > acct.balance:
            j = juice_insurance
            a = amount
            b = acct.balance
            msg = "Amount %d, insurance, %d, balance %d" % (a, j, b)
            raise InsufficientFundsError, msg
        if amount > cash.balance:
            msg = "Amount %d, cash balance %d" % (amount, cash.balance)
            raise InsufficientFundsError, msg
        with transaction.manager:
            acct = self.get_balance(account_id)
            wagers = self.get_balance(self.wagers.id)
            juice = self.get_balance(self.juice.id)
            cash = self.get_balance(self.cash.id)
            now = datetime.now()
            ttype = self._get_txn_type('place_bet')
            txn = Transaction()
            txn.type_id = ttype.id
            txn.created = now
            self.session.add(txn)
            txn = self.session.merge(txn)
            # transfer to wager
            # transfer from account
            to_wagers, from_acct = mkdbl_entries(txn,
                                                 self.wagers.id,
                                                 account_id,
                                                 amount,
                                                 now)
            
            # transfer to juice
            # account covers juice
            to_juice, juiced_from = mkdbl_entries(txn,
                                                  self.juice.id,
                                                  account_id,
                                                  juice_insurance,
                                                  now)
            # transfer to wager
            # transfer from cash
            cash_to_wagers, from_cash = mkdbl_entries(txn,
                                                      self.wagers.id,
                                                      self.cash.id,
                                                      amount,
                                                      now)
            dbobjects = [to_wagers, from_acct, to_juice, juiced_from,
                         cash_to_wagers, from_cash, txn]
            #adjust balances
            wagers.balance += amount + amount
            acct.balance -= amount
            cash.balance -= amount
            juice.balance += juice_insurance
            acct.balance -= juice_insurance
            # update database
            for dbobj in dbobjects:
                self.session.add(dbobj)
            for dbobj in [wagers, acct, cash, juice]:
                self.session.merge(dbobj)
        self._refresh_standard_accounts()
        return self.session.merge(txn)
    
    


    # This moves money from the
    # wagers account to the user
    # account.
    # Also, it moves an appropriate amount of
    # money from the juice account to the
    # user account.
    def win_bet(self, account_id, amount):
        acct = self.get_balance(account_id)
        wagers = self.get_balance(self.wagers.id)
        juice = self.get_balance(self.juice.id)
        juice_insurance = amount / 10
        total = amount + juice_insurance
        if amount > wagers.balance:
            msg = "Amount %d, balance %d" % (amount, wagers.balance)
            raise InsufficientFundsError, msg
        if juice_insurance > juice.balance:
            msg = "Juice %d, balance %d" % (juice_insurance, juice.balance)
            raise InsufficientFundsError, msg
        with transaction.manager:
            now = datetime.now()
            ttype = self._get_txn_type('win_bet')
            txn = Transaction()
            txn.type_id = ttype.id
            txn.created = now
            self.session.add(txn)
            txn = self.session.merge(txn)
            # transfer to user
            # transfer from wagers
            payout = amount + amount
            to_acct, from_wagers = mkdbl_entries(txn,
                                                 account_id,
                                                 self.wagers.id,
                                                 payout, now)
            

            # juice to user
            # juice from juice
            juiced_to, from_juice = mkdbl_entries(txn,
                                                  account_id,
                                                  self.juice.id,
                                                  juice_insurance,
                                                  now)
            # make object list
            dbobjects = [to_acct, from_wagers, from_juice, juiced_to, txn]
            # adjust balances
            acct.balance += payout
            wagers.balance -= payout
            acct.balance += juice_insurance
            juice.balance -= juice_insurance
            # update database
            for dbobj in dbobjects:
                self.session.add(dbobj)
            for dbobj in [acct, wagers, juice]:
                self.session.merge(dbobj)
        self._refresh_standard_accounts()
        return self.session.merge(txn)
    
    
            
    # This moves money from the
    # wagers account to the cash account
    # and also moves an appropriate amount
    # of money from the juice account to the
    # cash account.
    def lose_bet(self, amount):
        cash = self.get_balance(self.cash.id)
        wagers = self.get_balance(self.wagers.id)
        juice = self.get_balance(self.juice.id)
        juice_insurance = amount / 10
        total = amount + juice_insurance
        with transaction.manager:
            now = datetime.now()
            ttype = self._get_txn_type('lose_bet')
            txn = Transaction()
            txn.type_id = ttype.id
            txn.created = now
            self.session.add(txn)
            txn = self.session.merge(txn)
            payback = amount + amount
            to_cash, from_wagers = mkdbl_entries(txn,
                                                 self.cash.id,
                                                 self.wagers.id,
                                                 payback,
                                                 now)
            get_juice, juiced_from = mkdbl_entries(txn,
                                                   self.cash.id,
                                                   self.juice.id,
                                                   juice_insurance,
                                                   now)
            dbobjects = [to_cash, from_wagers, get_juice, juiced_from, txn]
            # adjust balances
            cash.balance += payback
            wagers.balance -= payback
            cash.balance += juice_insurance
            juice.balance -= juice_insurance
            for dbobj in dbobjects:
                self.session.add(dbobj)
            for dbobj in [cash, wagers, juice]:
                self.session.merge(dbobj)
        self._refresh_standard_accounts()
        return self.session.merge(txn)

    # This moves money from the
    # wagers account back to the
    # user and cash accounts, and
    # also removes an appropriate
    # amount of money from the juice
    # back to the user account.
    # This is the opposite of place_bet.
    def push_bet(self, account_id, amount):
        acct = self.get_balance(account_id)
        cash = self.get_balance(self.cash.id)
        wagers = self.get_balance(self.wagers.id)
        juice = self.get_balance(self.juice.id)
        juice_insurance = amount / 10
        total = amount + juice_insurance
        with transaction.manager:
            now = datetime.now()
            ttype = self._get_txn_type('push_bet')
            txn = Transaction()
            txn.type_id = ttype.id
            txn.created = now
            self.session.add(txn)
            txn = self.session.merge(txn)
            wagers_loss = amount + amount
            # transfer from wagers to account
            to_acct, from_wagers = mkdbl_entries(txn,
                                                 account_id,
                                                 self.wagers.id,
                                                 amount,
                                                 now)
            # transfer from wagers to cash
            to_cash, cfrom_wagers = mkdbl_entries(txn,
                                                  self.cash.id,
                                                  self.wagers.id,
                                                  amount,
                                                  now)
            # transfer from juice to account
            jto_acct, from_juice = mkdbl_entries(txn,
                                                 account_id,
                                                 self.juice.id,
                                                 juice_insurance,
                                                 now)
            dbobjects = [to_acct, from_wagers, to_cash, cfrom_wagers,
                         jto_acct, from_juice, txn]
            # adjust balances
            acct.balance += amount
            cash.balance += amount
            wagers.balance -= wagers_loss
            acct.balance += juice_insurance
            juice.balance -= juice_insurance
            for dbobj in dbobjects:
                self.session.add(dbobj)
            for dbobj in [acct, cash, wagers, juice]:
                self.session.merge(dbobj)
        self._refresh_standard_accounts()
        return self.session.merge(txn)

    def get_txn_types(self):
        q = self.session.query(TransactionType)
        ttypes = q.all()
        items = ((tt.id, tt.name) for tt in ttypes)
        return dict(items)
    
    
    def get_all_transfers(self):
        q = self.session.query(BaseTransfer)
        q = q.order_by(BaseTransfer.created)
        return q.all()
    

    def get_transfers(self, txn_id):
        q = self.session.query(BaseTransfer)
        q = q.filter_by(txn_id=txn_id)
        q = q.order_by(BaseTransfer.created)
        return q.all()

    def get_all_transactions(self):
        q = self.session.query(Transaction)
        q = q.order_by(Transaction.created)
        return q.all()

    def get_txns_by_ttype_id(self):
        pass

    
    def get_max_bet(self, account_id):
        return determine_max_bet(self.get_balance(account_id).balance)
    
