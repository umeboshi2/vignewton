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
from vignewton.managers.base import InsufficientFundsError

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

def get_context_from_current_bet(cb, odds):
    if cb.bet_type == 'underover':
        return cb.underover
    else:
        team_id = cb.team_id
        if team_id == odds.favored_id:
            return 'favored'
        else:
            return 'underdog'
        

class NFLBetFrag(BaseViewer):
    def __init__(self, request):
        super(NFLBetFrag, self).__init__(request)
        #self._template = 'vignewton:templates/main-betgame-frag.mako'
        #self.bets = BetsManager(self.request.db)
        self.render_frag()
        
    def render_frag(self):
        schema = CreditAmountSchema()
        form = deform.Form(schema, buttons=('submit',))
        self.layout.resources.deform_auto_need(form)
        self.response = form.render()
        
    
class NFLGameBetsViewer(BaseViewer):
    def __init__(self, request):
        super(NFLGameBetsViewer, self).__init__(request)
        self.layout.main_menu = make_main_menu(self.request).render()
        self.layout.ctx_menu = make_ctx_menu(self.request).output()

        self.teams = NFLTeamManager(self.request.db)
        self.games = NFLGameManager(self.request.db)
        self.odds = NFLOddsManager(self.request.db)
        self.bets = BetsManager(self.request.db)

        # make form resources available
        schema = CreditAmountSchema()
        form = deform.Form(schema, buttons=('submit',))
        self.layout.resources.deform_auto_need(form)
        del schema, form
        
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
            showbet=self.show_current_bet,
            cancelbet=self.place_bet_cancel,
            confirmbet=self.place_bet_confirm,
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


    def show_current_bet(self):
        user_id = self.get_current_user_id()
        current, odata = self.bets.show_requested_bet(user_id)
        amount = current.amount
        odds = self.odds.get(current.game_id)
        game = odds.game
        context = get_context_from_current_bet(current, odds)
        bettype, gameline, betline = self._get_misc_data(odds, game, context)
        template = 'vignewton:templates/main-place-bet-ask-confirm.mako'
        confirm_url = self.url(context='confirmbet', id='bet')
        cancel_url = self.url(context='cancelbet', id='bet')
        env = dict(amount=amount, gameline=gameline,
                   betline=betline,
                   odds=odds,
                   game=game,
                   confirm_url=confirm_url,
                   cancel_url=cancel_url,)
        content = self.render(template, env)
        self.layout.resources.main_betgames_confirm_bet.need()
        self.layout.content = content
        
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
        if CONTEXT_BETTYPE[context] == 'line':
            if context == 'favored':
                pick = self.teams.get(odds.favored_id)
            else:
                pick = self.teams.get(odds.underdog_id)
        else:
            pick = context
        try:
            self.bets.request_bet(user_id, game.id, amount, bettype, pick)
        except InsufficientFundsError, e:
            self.layout.content = str(e)
            return
        self.show_current_bet()

        
    def place_bet_confirm(self):
        user_id = self.get_current_user_id()
        self.bets.place_requested_bet(user_id)
        self.response = HTTPFound('/')

    def place_bet_cancel(self):
        user_id = self.get_current_user_id()
        self.bets.cancel_requested_bet(user_id)
        self.response = HTTPFound('/')
        
        
    
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
        
        
        
