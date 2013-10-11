from datetime import datetime, date, timedelta

from docutils.core import publish_parts

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
#from pyramid.security import authenticated_userid
from pyramid.renderers import render
from pyramid.response import Response

import colander
import deform


from trumpet.views.menus import BaseMenu

from vignewton.managers.nflgames import NFLGameManager
from vignewton.managers.odds import NFLOddsManager
from vignewton.managers.bets import BetsManager
from vignewton.managers.bets import NoCurrentBetError
from vignewton.managers.util import BettableGamesCollector

from vignewton.views.base import BaseViewer
from vignewton.views.base import make_main_menu, make_ctx_menu
from vignewton.views.schema import CreditAmountSchema

class MainCalJSONViewer(BaseViewer):
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
        url = self.request.route_url('vig_nflgames', context='viewgame',
                                     id=game.id)
        data = dict(title=game.summary, start=game.start.isoformat(),
                    end=game.end.isoformat(), url=url)
        return data
    
    
    def get_everthing(self):
        start, end = self._get_start_end()
        serialize = self.serialize_game_for_calendar
        nfl_games = self.nfl_games.get_games(start, end, timestamps=True)
        self.response = [serialize(g) for g in nfl_games]
        
        
    
class MainViewer(BaseViewer):
    def __init__(self, request):
        super(MainViewer, self).__init__(request)
        self.route = self.request.matched_route.name
        self.layout.main_menu = make_main_menu(self.request).render()
        self.layout.ctx_menu = make_ctx_menu(self.request).output()

        self.odds = NFLOddsManager(self.request.db)
        self.bets = BetsManager(self.request.db)
        
        # make form resources available
        schema = CreditAmountSchema()
        form = deform.Form(schema, buttons=('submit',))
        self.layout.resources.deform_auto_need(form)
        del schema, form
        
        # begin dispatch
        if self.route == 'home':
            self.main_view()
            return
        if self.route == 'main':
            self.context = self.request.matchdict['context']
        

        # make dispatch table
        self._cntxt_meth = dict(
            main=self.main_view,
            schedcal=self.schedule_view,
            )

        if self.context in self._cntxt_meth:
            self._cntxt_meth[self.context]()
        else:
            msg = 'Undefined Context: %s' % self.context
            self.layout.content = '<b>%s</b>' % msg



    def main_view(self):
        authn_policy = self.request.context.authn_policy
        authn = authn_policy.authenticated_userid(self.request)
        if authn is None:
            url = self.request.route_url('login')
            content = '<a href="%s">Login</a>' % url
            self.layout.content = content
        else:
            admin_username = self.get_admin_username()
            if authn == admin_username:
                return self.main_admin_view()
            else:
                return self.main_authenticated_view()
        
    def main_authenticated_view(self):
        self.layout.header = 'NFL Bettable Games'
        user_id = self.get_current_user_id()
        try:
            current, odata = self.bets.show_requested_bet(user_id)
        except NoCurrentBetError:
            current = None
        if current is not None:
            rfun = self.request.route_url
            url = rfun('vig_betgames', context='showbet', id='user')
            self.response = HTTPFound(url)
            return
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
        #self.layout.resources.lightbox.need()
        self.layout.resources.main_betgames_view.need()
        
    def main_admin_view(self):
        self.layout.content = "Main Admin View"
        
        
    def schedule_view(self):
        content = "Schedule Page"
        self.layout.content = content
        self.layout.subheader = 'Vig Newton'
        self.layout.resources.main_calendar_view.need()
        self.layout.resources.cornsilk.need()
        
        template = 'vignewton:templates/mainview-calendar.mako'
        env = {}
        content = self.render(template, env)
        self.layout.content = content

