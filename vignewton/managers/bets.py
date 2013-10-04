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
    

    def _copy_current_odds(self, bet, odds):
        for field in ['favored_id', 'underdog_id', 'total',
                      'spread']:
            setattr(bet, field, getattr(odds, field))

    def _make_bet(self, bettype, user_id, game_id, amount, pick):
        with transaction.manager:
            odds = self._get_odds(game_id)
            now = datetime.now()
            bet = UserBet()
            bet.bet_type = bettype
            bet.created = now
            bet.user_id = user_id
            bet.amount = amount
            if bettype == 'line':
                # the pick is a team
                bet.team_id = pick.id
            else:
                # the pick is under/over
                bet.underover = pick
            self._copy_current_odds(bet, odds)
            self.session.add(bet)
        return self.session.merge(bet)
            
    def _check_amount(self, user_id, amount):
        acct = self.accounts.get(user_id)
        balance = acct.balance
        

    # pick is either an NFLTeam object, 'over', or 'under'
    def place_bet(self, user_id, game_id, amount,
                  bettype, pick):
        if bettype not in ['line', 'underover']:
            raise RuntimeError, "Bad bettype %s:" % bettype
        return self._make_bet(bettype, user_id, game_id, amount, pick)

        
    
