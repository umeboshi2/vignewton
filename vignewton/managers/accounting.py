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
from vignewton.models.main import Transfer, LedgerEntry
from vignewton.models.main import UserAccount

from vignewton.models.main import BetFinal, CashTransfer

from vignewton.managers.bets import BetsManager

class InsufficientFundsError(Exception):
    pass

class AmountTooHighError(Exception):
    pass


# When a user deposits money, both the balance of
# the cash box and the account balance increase by
# the amount of the deposit.
#
# The same is true of pay outs.  A CashTransfer
# with a positive amount is a deposit and a
# negative is a payout.
#
# When the admin deposits money, the only the balance
# of the cash box increases.
#
# When a bet is finalized, a determination about win or
# loss is made.
#
#
#
#

class AccountingManager(object):
    def __init__(self, session):
        self.session = session
        self.db_account = Account
        self.db_transfer = CashTransfer
        self.db_final = BetFinal
        self.db_account_bal = AccountBalance
        self.db_bal = self.db_account_bal
        try:
            self.cash = self._get_cash_account()
        except NoResultFound:
            self.cash = None
        self.cash_minimum = 500
        self.bets = BetsManager(self.session)
        
    def _get_cash_account(self):
        q = self.session.query(Account)
        q = q.filter_by(name='Cash')
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

    def get_balance(self, account_id):
        q = self.session.query(AccountBalance)
        return q.get(account_id)
    
    def add_to_cash(self, amount):
        if amount <= 0:
            raise InsufficientFundsError, 'bad amount %d' % amount
        with transaction.manager:
            b = self.get_balance(self.cash.id)
            now = datetime.now()
            ct = CashTransfer()
            ct.account_id = self.cash.id
            ct.amount = amount
            ct.created = now
            ct.cash_balance = b.balance
            self.session.add(ct)
            b.balance += amount
            b = self.session.merge(b)
        return self.session.merge(ct), b


    def deposit_to_account(self, account_id, amount):
        if amount <= 0:
            raise InsufficientFundsError, "bad amount %d" % amount
        with transaction.manager:
            cash_balance = self.get_balance(self.cash.id)
            b = self.get_balance(account_id)
            now = datetime.now()
            ct = CashTransfer()
            ct.account_id = account_id
            ct.amount = amount
            ct.cash_balance = cash_balance.balance
            ct.created = now
            self.session.add(ct)
            b.balance += amount
            b = self.session.merge(b)
            cash_balance.balance += amount
            cash_balance = self.session.merge(cash_balance)
        return self.session.merge(ct), b

    
    
    def pay_account(self, account_id, amount):
        cash_balance = self.get_balance(self.cash.id)
        balance = self.get_balance(account_id)
        if amount > 0:
            amount = -amount
        if cash_balance.balance + amount <= self.cash_minimum:
            msg = "cash: %d, amount %d" % (cash_balance.balance, amount)
            raise InsufficientFundsError, msg

        
        new_balance = balance.balance + amount
        new_cash_balance = cash_balance.balance + amount
        if new_balance < 0:
            msg = "balance %d, amount %d" % (balance.balance, amount)
            raise AmountTooHighError, msg
        
        with transaction.manager:
            now = datetime.now()
            ct = CashTransfer()
            ct.account_id = account_id
            ct.amount = amount
            ct.created = now
            ct.cash_balance = cash_balance.balance
            balance.balance = new_balance
            cash_balance.balance = new_cash_balance
            balance = self.session.merge(balance)
            cash_balance = self.session.merge(cash_balance)
            self.session.add(ct)
        return self.session.merge(ct), balance

    def get_all_cash_transfers(self):
        q = self.session.query(CashTransfer)
        return q.all()
    
    def pay_bet(self, bet_id):
        pass
    
