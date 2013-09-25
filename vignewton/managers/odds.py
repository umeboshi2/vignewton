import csv
import re
from datetime import datetime, timedelta

import requests
import transaction
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import or_

from vignewton.models.main import NFLOddsData, NFLGameOdds
from vignewton.models.main import NFLGame

from vignewton.managers.nflgames import NFLGameManager, NFLTeamManager
from vignewton.managers.oddsparser import NFLOddsParser
from vignewton.managers.oddsparser import parse_odds_html

ten_minutes = timedelta(minutes=10)
odds_ttl = ten_minutes

class NFLOddsCache(object):
    def __init__(self, session):
        self.session = session

    def set_url(self, url):
        self.url = url

    def query(self):
        q = self.session.query(NFLOddsData)
        return q

    def get(self, id):
        return self.query().get(id)

    def _get_latest(self):
        q = self.query()
        q = q.order_by(NFLOddsData.retrieved.desc())
        return q.first()

    def _add(self):
        r = requests.get(self.url)
        games = parse_odds_html(r.text)
        now = datetime.now()
        with transaction.manager:
            data = NFLOddsData()
            data.retrieved = now
            data.content = games
            self.session.add(data)
        return self.session.merge(data)
    
    def get_latest(self):
        updated = False
        now = datetime.now()
        latest = self._get_latest()
        if latest is None or now - latest.retrieved >= odds_ttl:
            latest = self._add()
            updated = True
        return latest, updated
    
        
    
        
    

    

class NFLOddsManager(object):
    def __init__(self, session):
        self.session = session
        self.games = NFLGameManager(self.session)
        self.teams = NFLTeamManager(self.session)
        self.oddscache = NFLOddsCache(self.session)

    def query(self):
        return self.session.query(NFLGameOdds)

    def get(self, game_id):
        return self.query().get(game_id)
    
    def get_odds(self, game_id):
        q = self.query()
        q.filter_by(game_id=game_id)
        return q.one()

    def add_game_odds(self, game_id, game):
        favored_id = self.teams.get_by_name(game['favored']).id
        underdog_id = self.teams.get_by_name(game['underdog']).id
        underover = game['favored_odds']
        spread = game['underdog_odds']
        now = datetime.now()
        with transaction.manager:
            odds = NFLGameOdds()
            odds.game_id = game_id
            odds.retrieved = now
            odds.favored_id = favored_id
            odds.underdog_id = underdog_id
            odds.underover = underover
            odds.spread = spread
            self.session.add(odds)
        return self.session.merge(odds)

    def update_game_odds(self, game_id, game, odds):
        underover = game['favored_odds']
        spread = game['underdog_odds']
        now = datetime.now()
        with transaction.manager:
            odds.retrieved = now
            odds.underover = underover
            odds.spread = spread
            odds = self.session.merge(odds)
        return odds
    
        
    def update_current_odds(self):
        latest, updated = self.oddscache.get_latest()
        oddslist = list()
        for game in latest.content:
            game_id = self.games.get_game_from_odds(game).id
            odds = self.get(game_id)
            if odds is None:
                odds = self.add_game_odds(game_id, game)
            else:
                odds = self.update_game_odds(game_id, game, odds)
            oddslist.append(odds)
        oddslist = [self.session.merge(o) for o in oddslist]
        return oddslist, updated

    def get_current_odds(self):
        now = datetime.now()
        q = self.query()
        q = q.filter(NFLGame.start >= now)
        return q.all()
    
    
                

    
        
    
