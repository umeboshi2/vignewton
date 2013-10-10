from datetime import datetime, date, timedelta

from docutils.core import publish_parts

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import authenticated_userid
from pyramid.renderers import render
from pyramid.response import Response

from trumpet.views.base import BaseMenu


from vignewton.managers.nflgames import NFLGameManager
from vignewton.managers.odds import NFLOddsManager
from vignewton.managers.bets import BetsManager

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
    url = request.route_url(route, context='bets', id='bets')
    menu.append_new_entry('Determine Bets', url)
    
    
    
class UpdateDBViewer(AdminViewer):
    def __init__(self, request):
        super(UpdateDBViewer, self).__init__(request)
        #self.layout.main_menu = make_main_menu(self.request).render()
        #self.layout.ctx_menu = make_ctx_menu(self.request).output()
        make_context_menu(self.request)
        
        self.games = NFLGameManager(self.request.db)
        self.odds = NFLOddsManager(self.request.db)
        self.bets = BetsManager(self.request.db)
        
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
            bets=self.determine_bets,
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
            

    def determine_bets(self):
        template = 'vignewton:templates/admin-determine-bets.mako'
        clist = self.bets.determine_bets()
        env = dict(bm=self.bets, clist=clist)
        content = self.render(template, env)
        self.layout.content = content
        
