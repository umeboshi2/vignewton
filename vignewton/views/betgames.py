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
from vignewton.managers.bets import BetsManager
from vignewton.managers.util import BettableGamesCollector

from vignewton.views.base import BaseViewer
from vignewton.views.base import make_main_menu, make_ctx_menu

def text_for_line_bet(odds, game, betval):
    gameline = "%s at %s" % (game.summary, game.start.isoformat())
    points = 'than %d points.' % odds.spread
    team = getattr(odds, betval).name
    teampart = 'Betting on %s, %s,' % (betval, team)
    if betval == 'underdog':
        betline = '%s to either win or be beaten by less %s' % (teampart, points)
    elif betval == 'favored':
        betline = '%s to win by more %s' % (teampart, points)
    else:
        raise RuntimeError, "Bad betval %s" % betval
    return gameline, betline

def text_for_underover_bet(odds, game, betval):
    gameline = "%s at %s" % (game.summary, game.start.isoformat())
    points = ' %d points.' % odds.total
    prefix = "Betting on total points by both teams to be %s" % betval
    betline = '%s %s' % (prefix, points)
    return gameline, betline

    

class NFLGameBetsViewer(BaseViewer):
    def __init__(self, request):
        super(NFLGameBetsViewer, self).__init__(request)
        self.layout.main_menu = make_main_menu(self.request).render()
        self.layout.ctx_menu = make_ctx_menu(self.request).output()

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
            viewgame=self.view_game,
            betover=self.place_bet,
            betunder=self.place_bet,
            betfavored=self.place_bet,
            betunderdog=self.place_bet,
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
        collector = BettableGamesCollector(olist)
        dates = collector.dates.keys()
        dates.sort()
        game_date_format = '%A - %B %d'
        template = 'vignewton:templates/main-betgames-view.mako'
        env = dict(collector=collector, dates=dates,
                   game_date_format=game_date_format)
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
        
    def place_bet(self):
        game_id = self.request.matchdict['id']
        context = self.request.matchdict['context']
        if context[:3] == 'bet':
            context = context[3:]
            if context not in ['under', 'over', 'favored', 'underdog']:
                raise RuntimeError, "Bad Context %s" % context
        else:
            raise RuntimeError, "Bad Context %s" % context
        odds = self.odds.get_odds(game_id)
        game = odds.game
        if context in ['favored', 'underdog']:
            bettype = 'line'
            gameline, betline = text_for_line_bet(odds, game, context)
            content = '%s<br>%s' % (gameline, betline)
        else:
            gameline, betline = text_for_underover_bet(odds, game, context)
            content = '%s<br>%s' % (gameline, betline)
        self.layout.content = content
        
        
