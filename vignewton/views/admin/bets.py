from datetime import datetime, date, timedelta

from docutils.core import publish_parts

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import authenticated_userid
from pyramid.renderers import render
from pyramid.response import Response

from trumpet.views.base import BaseMenu


from vignewton.managers.nflgames import NFLGameManager
from vignewton.managers.nflgames import NFLTeamManager
from vignewton.managers.bets import BetsManager
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
    route = 'admin_bets'
    url = request.route_url(route, context='main', id=None)
    menu.append_new_entry('Main View', url)
    url = request.route_url(route, context='allpending', id='cash')
    menu.append_new_entry('Pending Bets', url)
    url = request.route_url(route, context='allclosed', id='cash')
    menu.append_new_entry('Closed Bets', url)
    
    
class BetsViewer(AdminViewer):
    def __init__(self, request):
        super(BetsViewer, self).__init__(request)
        #self.layout.main_menu = make_main_menu(self.request).render()
        #self.layout.ctx_menu = make_ctx_menu(self.request).output()
        make_context_menu(self.request)
        
        self.accounts = AccountingManager(self.request.db)
        
        self.teams = NFLTeamManager(self.request.db)
        self.games = NFLGameManager(self.request.db)
        self.odds = NFLOddsManager(self.request.db)
        self.bets = BetsManager(self.request.db)
        
        settings = self.get_app_settings()
        url = settings['vignewton.nfl.odds.url']
        self.odds.oddscache.set_url(url)
        
        self.context = self.request.matchdict['context']
        # make dispatch table
        self._cntxt_meth = dict(
            main=self.main_view,
            allpending=self.view_all_pending_bets,
            allclosed=self.view_all_closed_bets,
            )

        if self.context in self._cntxt_meth:
            self._cntxt_meth[self.context]()
        else:
            msg = 'Undefined Context: %s' % self.context
            self.layout.content = '<b>%s</b>' % msg


    def main_view(self):
        self.layout.content = 'Main Bets View'

    def view_all_pending_bets(self):
        template = 'vignewton:templates/admin-view-all-pending-bets.mako'
        bets = self.bets.get_all_bets()
        env = dict(bets=bets)
        content = self.render(template, env)
        self.layout.content = content

    def view_all_closed_bets(self):
        self.layout.content = 'View Closed Bets'
        
