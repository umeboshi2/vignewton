from datetime import datetime, date, timedelta

from docutils.core import publish_parts

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import authenticated_userid
from pyramid.renderers import render
from pyramid.response import Response

from trumpet.views.base import BaseMenu


from vignewton.managers.nflgames import NFLGameManager
from vignewton.managers.nflgames import NFLTeamManager
from vignewton.managers.odds import NFLOddsManager
from vignewton.managers.util import BettableGamesCollector
from vignewton.managers.accounting import AccountingManager

from vignewton.views.base import make_main_menu, make_ctx_menu
from vignewton.views.base import AdminViewer
from vignewton.views.base import get_regular_users
from vignewton.views.schema import deferred_choices, make_select_widget
from vignewton.views.schema import CreditAmountSchema
from vignewton.views.schema import AccountCreditAmountSchema

import colander
import deform
    
    
def make_context_menu(request):
    layout = request.layout_manager.layout
    menu = layout.ctx_menu
    route = 'admin_credits'
    url = request.route_url(route, context='main', id=None)
    menu.append_new_entry('Cash Report', url)
    url = request.route_url(route, context='cashdeposit', id='cash')
    menu.append_new_entry('Deposit Cash', url)
    url = request.route_url(route, context='cashwithdraw', id='cash')
    menu.append_new_entry('Withdraw Cash', url)
    url = request.route_url(route, context='acctdeposit', id='somebody')
    menu.append_new_entry('Credit Account', url)
    url = request.route_url(route, context='acctwithdraw', id='somebody')
    menu.append_new_entry('Pay Account', url)
    url = request.route_url(route, context='lsxfers', id='xfer')
    menu.append_new_entry('List Transfers', url)
    
class CreditsViewer(AdminViewer):
    def __init__(self, request):
        super(CreditsViewer, self).__init__(request)
        #self.layout.main_menu = make_main_menu(self.request).render()
        #self.layout.ctx_menu = make_ctx_menu(self.request).output()
        make_context_menu(self.request)
        
        self.accounts = AccountingManager(self.request.db)
        
        self.teams = NFLTeamManager(self.request.db)
        self.games = NFLGameManager(self.request.db)
        self.odds = NFLOddsManager(self.request.db)

        settings = self.get_app_settings()
        url = settings['vignewton.nfl.odds.url']
        self.odds.oddscache.set_url(url)
        
        self.context = self.request.matchdict['context']
        # make dispatch table
        self._cntxt_meth = dict(
            main=self.main_view,
            view=self.view_account,
            cashdeposit=self.deposit_cash,
            cashwithdraw=self.withdraw_cash,
            acctdeposit=self.deposit_account_main,
            acctwithdraw=self.withdraw_account_main,
            lsxfers=self.list_transfers,
            )

        if self.context in self._cntxt_meth:
            self._cntxt_meth[self.context]()
        else:
            msg = 'Undefined Context: %s' % self.context
            self.layout.content = '<b>%s</b>' % msg


    def main_view(self):
        self.layout.header = 'Main Credits View'
        self.layout.content = 'Main Credits View'
        template = 'vignewton:templates/admin-cash-report.mako'
        env = dict(accounts=self.accounts)
        content = self.render(template, env)
        #self.layout.content = "Deposit %d into cash box" % amount
        self.layout.content = content

            
    def view_account(self):
        txt = "View Account"
        self.layout.header = txt
        self.layout.content = txt

    def _cash_form_submitted(self, form, transfer):
        self.layout.subheader = "attempting to deposit cash"
        controls = self.request.POST.items()
        try:
            data = form.validate(controls)
        except deform.ValidationFailure, e:
            self.layout.content = e.render()
            return
        amount = int(data['amount'])
        if transfer == 'deposit':
            cash, wild = self.accounts.add_to_cash(amount)
        elif transfer == 'withdraw':
            cash, wild = self.accounts.take_from_cash(amount)
        else:
            raise RuntimeError, "bad problem"
        template = 'vignewton:templates/admin-cash-report.mako'
        env = dict(cash=cash, wild=wild, accounts=self.accounts)
        content = self.render(template, env)
        #self.layout.content = "Deposit %d into cash box" % amount
        self.layout.content = content
        
            
    
    def deposit_cash(self):
        schema = CreditAmountSchema()
        form = deform.Form(schema, buttons=('submit',))
        if 'submit' in self.request.POST:
            self._cash_form_submitted(form, 'deposit')
        else:
            formdata = dict()
            self.layout.content = form.render(formdata)

    def withdraw_cash(self):
        schema = CreditAmountSchema()
        form = deform.Form(schema, buttons=('submit',))
        if 'submit' in self.request.POST:
            self._cash_form_submitted(form, 'withdraw')
        else:
            formdata = dict()
            self.layout.content = form.render(formdata)


    def _acct_form_submitted(self, form, transfer):
        self.layout.subheader = "attempting to deposit cash"
        controls = self.request.POST.items()
        try:
            data = form.validate(controls)
        except deform.ValidationFailure, e:
            self.layout.content = e.render()
            return
        amount = int(data['amount'])
        user_id = data['user']
        account = self.accounts.get(user_id)
        if transfer == 'deposit':
            ignore = self.accounts.deposit_to_account(account.id, amount)
        elif transfer == 'withdraw':
            ignore = self.accounts.pay_account(account.id, amount)
        else:
            raise RuntimeError, "bad problem"
        template = 'vignewton:templates/admin-cash-report.mako'
        env = dict(accounts=self.accounts)
        content = self.render(template, env)
        #self.layout.content = "Deposit %d into cash box" % amount
        self.layout.content = content


    def _main_handle_account_form(self, transfer):
        schema = AccountCreditAmountSchema()
        users = get_regular_users(self.request)
        choices = [(u.id, u.username) for u in users]
        schema['user'].widget = make_select_widget(choices)
        form = deform.Form(schema, buttons=('submit',))
        if 'submit' in self.request.POST:
            self._acct_form_submitted(form, transfer)
        else:
            formdata = dict()
            self.layout.content = form.render(formdata)
        
    def deposit_account_main(self):
        return self._main_handle_account_form('deposit')

    def withdraw_account_main(self):
        return self._main_handle_account_form('withdraw')
        
    def list_transfers(self):
        template = 'vignewton:templates/admin-list-transfers.mako'
        transfers = self.accounts.get_all_transfers()
        env = dict(am=self.accounts)
        content = self.render(template, env)
        self.layout.content = content
        
