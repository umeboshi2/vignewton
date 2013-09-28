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



class AccountingManager(object):
    def __init__(self, session):
        self.session = session
        self.db_account = Account
        self.db_transfer = Transfer
        self.db_ledger_entry = LedgerEntry
        self.db_account_bal = AccountBalance
        

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
    

    def add_transfer(self, name):
        with transaction.manager:
            t = Transfer()
            t.name = name
            self.session.add(t)
        return self.session.merge(t)
    
    def get_transfer_by_name(self, name):
        q = self.session.query(Transfer)
        q = q.filter_by(name=name)
        return q.one()
    
    def transfer_income_to_account(self, account_id, amount):
        pass
    
    
