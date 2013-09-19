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

from vignewton.views.base import BaseViewer
from vignewton.views.base import make_main_menu, make_ctx_menu

class GameCalJSONViewer(BaseViewer):
    def __init__(self, request):
        super(MainCalJSONViewer, self).__init__(request)
        self.nfl_games = NFLGameManager(self.request.db)
        self.get_everthing()

    def _get_start_end_userid(self, user_id=True):
        start = self.request.GET['start']
        end = self.request.GET['end']
        if user_id:
            user_id = self.request.session['user'].id
        return start, end, user_id

    def _get_start_end(self):
        start = self.request.GET['start']
        end = self.request.GET['end']
        return start, end
        
    def serialize_game_for_calendar(self, game):
        data = dict(title=game.summary, start=game.start.isoformat(),
                    end=game.end.isoformat())
        return data
    
    
    def get_everthing(self):
        start, end = self._get_start_end()
        serialize = self.serialize_game_for_calendar
        nfl_games = self.nfl_games.get_games(start, end, timestamps=True)
        self.response = [serialize(g) for g in nfl_games]
        
        
    
class NFLGameViewer(BaseViewer):
    def __init__(self, request):
        super(NFLGameViewer, self).__init__(request)
        self.layout.main_menu = make_main_menu(self.request).render()
        self.layout.ctx_menu = make_ctx_menu(self.request).output()

        self.teams = NFLTeamManager(self.request.db)
        self.games = NFLGameManager(self.request.db)
        
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

            
    def main_view(self):
        self.layout.subheader = 'NFL Teams' 
        teams = self.teams.all()
        template = 'vignewton:templates/main-nfl-teams-view.mako'
        env = dict(teams=teams)
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
        
        
        
