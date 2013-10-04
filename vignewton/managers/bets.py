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
from vignewton.models.main import UserAccount, UserBet
from vignewton.models.main import BetHistory

from vignewton.managers.nflgames import NFLGameManager, NFLTeamManager
from vignewton.managers.odds import NFLOddsManager
from vignewton.managers.accounting import AccountingManager


class BetsManager(object):
    def __init__(self, session):
        self.session = session
        self.games = NFLGameManager(self.session)
        self.teams = NFLTeamManager(self.session)
        self.odds = NFLOddsManager(self.session)
        self.accounts = AccountingManager(self.session)
        
    def query(self):
        return self.session.query(UserBet)

    def get(self, bet_id):
        return self.query().get(bet_id)

    def _get_odds(self, game_id):
        odds = self.odds.get_odds(game_id)
        return odds
    
    
    def _make_line_bet(self, user_id, game_id, amount, team):
        with transaction.manager:
            odds = self.odds.get_odds(game_id)
            now = datetime.now()
            bet = UserBet()
            bet.bet_type = 'line'
            bet.created = now
            bet.user_id = user_id
            bet.amount = amount
            

    def _make_underover_bet(self, user_id, game_id, amount, underover):
        pass

    def _check_amount(self, user_id, amount):
        pass
    
    def place_bet(self, user_id, game_id, amount,
                  bettype, team=None, underover='under'):
        if bettype == 'line':
            return self._make_line_bet(self, user_id, game_id, amount, team)
        elif bettype == 'underover':
            return self._make_underover_bet(user_id,
                                            game_id, amount, underover)
        else:
            raise RuntimeError, "Bad bettype %s:" % bettype
        
    
