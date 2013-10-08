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
from vignewton.views.schema import CreditAmountSchema

CONTEXT_BETTYPE = dict(over='underover', under='underover',
                       underdog='line', favored='line')


def text_for_line_bet(odds, game, betval):
    game_date_format = '%A - %B %d'
    game_start = game.start.strftime(game_date_format)
    gameline = "%s at %s" % (game.summary, game_start)
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
    game_date_format = '%A - %B %d'
    game_start = game.start.strftime(game_date_format)
    gameline = "%s at %s" % (game.summary, game_start)
    points = ' %d points.' % odds.total
    prefix = "Betting on total points by both teams to be %s" % betval
    betline = '%s %s' % (prefix, points)
    return gameline, betline

CONTEXT_TEXTFUN = dict(line=text_for_line_bet,
                       underover=text_for_underover_bet)


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

    def _get_bet_context(self):
        context = self.request.matchdict['context']
        if context[:3] == 'bet':
            context = context[3:]
            if context not in CONTEXT_BETTYPE:
                raise RuntimeError, "Bad Context %s" % context
        else:
            raise RuntimeError, "Bad Context %s" % context
        return context

    def _get_misc_data(self, odds, game, context):
        bettype = CONTEXT_BETTYPE[context]
        gameline, betline = CONTEXT_TEXTFUN[bettype](odds, game, context)
        return bettype, gameline, betline
    
    def _place_bet_submitted(self, form, odds, game):
        controls = self.request.POST.items()
        try:
            data = form.validate(controls)
        except deform.ValidationFailure, e:
            self.layout.content = e.render()
            return
        amount = int(data['amount'][1:])
        user_id = self.get_current_user_id()
        context = self._get_bet_context()
        bettype, gameline, betline = self._get_misc_data(odds, game, context)
        template = 'vignewton:templates/main-place-bet-ask-confirm.mako'
        url = '#'
        env = dict(amount=amount, gameline=gameline,
                   betline=betline,
                   odds=odds,
                   game=game,
                   url=url)
        content = self.render(template, env)
        self.layout.resources.main_betgames_confirm_bet.need()
        self.layout.content = content
        #self.session['current_bettype'] = bettype
        #self.session['current_amount'] = amount
        #self.session['current_betval'] = context
        
    def place_bet_confirm(self):
        context = self._get_bet_context()
        game_id = self.request.matchdict['id']
        game = self.games.get(game_id)
        user_id = self.get_current_user_id()
        post = self.request.POST
        amount = int(post['amount'])
        #bettype = self.session['current_bettype']
        #amount = self.session['current_amount']
        #betval = self.session['current_betval']
        
        
    
    def place_bet(self):
        game_id = self.request.matchdict['id']
        odds = self.odds.get_odds(game_id)
        game = odds.game
        schema = CreditAmountSchema()
        form = deform.Form(schema, buttons=('submit',))
        self.layout.resources.deform_auto_need(form)
        if 'submit' in self.request.POST:
            self._place_bet_submitted(form, odds, game)
        else:
            context = self._get_bet_context()
            bettype, gameline, betline = self._get_misc_data(odds,
                                                             game, context)
            
            template = 'vignewton:templates/main-place-bet.mako'
            env = dict(form=form, gameline=gameline,
                       betline=betline,
                       odds=odds,
                       game=game)
            content = self.render(template, env)
            self.layout.content = content
        
        
        
