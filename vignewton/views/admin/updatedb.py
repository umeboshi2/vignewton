from datetime import datetime, date, timedelta

from docutils.core import publish_parts

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import authenticated_userid
from pyramid.renderers import render
from pyramid.response import Response

from trumpet.views.base import BaseMenu


from vignewton.managers.nflgames import NFLGameManager
from vignewton.managers.odds import NFLOddsManager

from vignewton.views.base import make_main_menu, make_ctx_menu
from vignewton.views.base import AdminViewer
from vignewton.views.base import get_regular_users
from vignewton.views.schema import deferred_choices, make_select_widget

import colander
import deform
    
    
def make_context_menu(request):
    layout = request.layout_manager.layout
    menu = layout.ctx_menu
    route = 'admin_updatedb'
    url = request.route_url(route, context='main', id=None)
    menu.append_new_entry('Main update view', url)
    url = request.route_url(route, context='games', id='cash')
    menu.append_new_entry('Update Game Schedule', url)
    url = request.route_url(route, context='odds', id='cash')
    menu.append_new_entry('Update Game Odds', url)
    
    
class UpdateDBViewer(AdminViewer):
    def __init__(self, request):
        super(UpdateDBViewer, self).__init__(request)
        #self.layout.main_menu = make_main_menu(self.request).render()
        #self.layout.ctx_menu = make_ctx_menu(self.request).output()
        make_context_menu(self.request)
        
        self.games = NFLGameManager(self.request.db)
        self.odds = NFLOddsManager(self.request.db)

        settings = self.get_app_settings()
        url = settings['vignewton.nfl.odds.url']
        self.odds.oddscache.set_url(url)
        url = settings['vignewton.nfl.schedule.url']
        self.games.schedules.set_url(url)
        
        self.context = self.request.matchdict['context']
        # make dispatch table
        self._cntxt_meth = dict(
            main=self.main_view,
            games=self.update_games,
            odds=self.update_odds,
            )

        if self.context in self._cntxt_meth:
            self._cntxt_meth[self.context]()
        else:
            msg = 'Undefined Context: %s' % self.context
            self.layout.content = '<b>%s</b>' % msg


    def main_view(self):
        self.layout.header = 'Main Update View'
        self.layout.content = 'Main Update View'


    def update_games(self):
        updated = self.games.update_games()
        if updated:
            self.layout.content = 'Game Schedule updated.'
        else:
            self.layout.content = 'No need to update yet.'

    def update_odds(self):
        olist, updated = self.odds.update_current_odds()
        if updated:
            self.layout.content = 'Game Odds updated.'
        else:
            self.layout.content = 'No need to update yet.'
            
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
        
