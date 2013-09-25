from datetime import datetime, date, timedelta

from docutils.core import publish_parts

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import authenticated_userid
from pyramid.renderers import render
from pyramid.response import Response

import colander
import deform


from trumpet.views.menus import BaseMenu

from vignewton.managers.nflgames import NFLGameManager
from vignewton.managers.nflgames import NFLTeamManager
from vignewton.managers.odds import NFLOddsManager

from vignewton.views.base import BaseViewer
from vignewton.views.base import make_main_menu, make_ctx_menu

class NFLGameBetsViewer(BaseViewer):
    def __init__(self, request):
        super(NFLGameBetsViewer, self).__init__(request)
        self.layout.main_menu = make_main_menu(self.request).render()
        self.layout.ctx_menu = make_ctx_menu(self.request).output()

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
            viewgame=self.view_game,
            )

        if self.context in self._cntxt_meth:
            self._cntxt_meth[self.context]()
        else:
            msg = 'Undefined Context: %s' % self.context
            self.layout.content = '<b>%s</b>' % msg


    def _update_odds(self):
        pass
    
    
    def main_view(self):
        self.layout.header = 'NFL Bettable Games' 
        olist = self.odds.get_current_odds()
        template = 'vignewton:templates/main-betgames-view.mako'
        env = dict(olist=olist)
        content = self.render(template, env)
        self.layout.content = content

    def view_game(self):
        id = self.request.matchdict['id']
        game = self.games.get(id)
        self.layout.content = '<pre>%s</pre>' % game.description
        #now = datetime.now()
        #template = 'vignewton:templates/view-nfl-team.mako'
        #env = dict(team=team, games=games, now=now)
        #content = self.render(template, env)
        #self.layout.content = content
        x = id
        
        
        
