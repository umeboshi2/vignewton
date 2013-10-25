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

from vignewton.models.main import UpdateReport

from vignewton.managers.nflgames import NFLGameManager
from vignewton.managers.odds import NFLOddsManager
from vignewton.managers.bets import BetsManager

def serialize_odds(odds):
    data = dict(game_id=odds.game_id,
                retrieved=odds.retrieved,
                favored_id=odds.favored_id,
                underdog_id=odds.underdog_id,
                total=odds.total,
                spread=odds.spread,)
    return data

def serialize_closed_bet(bet):
    if bet is None:
        return None
    data = dict(id=bet.id,
                user_id=bet.user_id,
                game_id=bet.game_id,
                bet_txn_id=bet.bet_txn_id,
                close_txn_id=bet.close_txn_id,
                created=bet.created,
                amount=bet.amount,
                bet_type=bet.bet_type,
                underover=bet.underover,
                team_id=bet.team_id,
                total=bet.total,
                spread=bet.spread,
                favored_id=bet.favored_id,
                underdog_id=bet.underdog_id,
                closed=bet.closed,
                status=bet.status,)
    return data

# arguments are db managers
def update_database(games, odds, bets):
    games_updated = games.update_games()
    oddslist, odds_updated = odds.update_current_odds()
    determined = bets.determine_bets()
    oddslist = [serialize_odds(o) for o in oddslist]
    determined = [serialize_closed_bet(b) for b in determined]
    data = dict(games_updated=games_updated,
                odds_updated=odds_updated,
                oddslist=oddslist, determined=determined)
    return data

class UpdateDBManager(object):
    def __init__(self, session):
        self.session = session
        self.games = NFLGameManager(self.session)
        self.odds = NFLOddsManager(self.session)
        self.bets = BetsManager(self.session)

    def set_schedule_url(self, url):
        self.games.schedules.set_url(url)

    def set_odds_url(self, url):
        self.odds.oddscache.set_url(url)
        
    def query(self):
        return self.session.query(UpdateReport)

    def get(self, report_id):
        return self.query().get(report_id)

    def _order_desc_filter(self, query):
        return query.order_by(UpdateReport.created.desc())
    
    def get_latest(self):
        q = self.query()
        q = self._order_desc_filter(q)
        return q.first()

    def get_all(self):
        q = self.query()
        q = self._order_desc_filter(q)
        return q.all()
    

    def _add_report(self, content):
        with transaction.manager:
            now = datetime.now()
            ur = UpdateReport()
            ur.created = now
            ur.content = content
            self.session.add(ur)
        return self.session.merge(ur)
    
    def _update_database(self):
        games_updated = self.games.update_games()
        #games_updated = False
        oddslist, odds_updated = self.odds.update_current_odds()
        determined = self.bets.determine_bets()
        oddslist = [serialize_odds(o) for o in oddslist]
        determined = [serialize_closed_bet(b) for b in determined]
        data = dict(games_updated=games_updated,
                    odds_updated=odds_updated,
                    oddslist=oddslist, determined=determined)
        return data

    def update(self):
        content = self._update_database()
        report = self._add_report(content)
        return report
    
    
