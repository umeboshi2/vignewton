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
from vignewton.models.main import ClosedBet
from vignewton.models.main import BetHistory

from vignewton.managers.base import InsufficientFundsError
from vignewton.managers.nflgames import NFLGameManager, NFLTeamManager
from vignewton.managers.odds import NFLOddsManager
from vignewton.managers.accounting import AccountingManager
from vignewton.managers.util import determine_max_bet

BETTYPES = ['underover', 'line']

WINLOSE = { True : 'win',
            False : 'lose'}


class BetNotInTensError(Exception):
    pass

# returns favored, underdog, push
# if the user bets according to the
# return of this function, they win.
def determine_line_bet(bet, fscore, uscore):
    if uscore >= fscore:
        return 'underdog'
    else:
        spread = fscore - uscore
        if spread == bet.spread:
            return 'push'
        elif spread > bet.spread:
            return 'favored'
        else:
            return 'underdog'
    raise RuntimeError, "Bad logic in determine_line_bet"

# returns win, lose, push
def determine_bet(bet, fscore, uscore):
    if bet.bet_type == 'underover':
        total = fscore + uscore
        if bet.total == total:
            return 'push'
        if bet.underover == 'under':
            return WINLOSE[total < bet.total]
        elif bet.underover == 'over':
            return WINLOSE[total > bet.total]
        else:
            raise RuntimeError, "bad underover"
    elif bet.bet_type == 'line':
        result = determine_line_bet(bet, fscore, uscore)
        if result == 'push':
            return 'push'
        elif result == 'favored':
            return WINLOSE[bet.favored_id == bet.team_id]
        elif result == 'underdog':
            return WINLOSE[bet.underdog_id == bet.team_id]
        else:
            raise RuntimeError, "bad logic in determine_bet(line)"
    else:
        raise RuntimeError, "Bad bet type %s" % bet.bet_type
    
        
def make_closed_bet(bet):
    cb = ClosedBet()
    

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

    def _check_amount(self, user_id, amount):
        if amount % 10 != 0:
            raise BetNotInTensError, "Bad amount %d" % amount
        acct = self.accounts.get(user_id)
        balance = acct.balance.balance
        max_bet = determine_max_bet(balance)
        if amount > max_bet:
            juice_insurance = amount / 10
            total = amount + juice_insurance
            msg = "Total needed %d, current balance %d" % (total, balance)
            raise InsufficientFundsError, msg
        return True

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

    # pick is either an NFLTeam object, 'over', or 'under'
    def place_bet(self, user_id, game_id, amount,
                  bettype, pick):
        # here we sanitize the bettype and
        # amount arguments
        if bettype not in ['line', 'underover']:
            raise RuntimeError, "Bad bettype %s:" % bettype
        # check amount
        # self.accounts.check_bet_amount(user_id, amount)
        self._check_amount(user_id, amount)
        
        return self._make_bet(bettype, user_id, game_id, amount, pick)

    def get_bets(self, user_id=None, game_id=None):
        pass

    def get_game_bets(self, game_id):
        q = self.query()
        q = q.filter_by(game_id=game_id)
        return q.all()
    

    def get_user_bets(self, user_id, game_id=None):
        q = self.query()
        q = q.filter_by(user_id=user_id)
        if game_id is not None:
            q = q.filter_by(game_id=game_id)
        return q.all()

    def _get_score(self, bet):
        "returns score as favored, underdog"
        game = bet.game
        score = game.score
        if bet.favored_id == game.away_id:
            favored_score = score.away_score
        elif bet.favored_id == game.home_id:
            favored_score = score.home_score
        else:
            raise RuntimeError, "Team/score mismatch game %d" % game.id
        if bet.underdog_id == game.away_id:
            underdog_score = score.away_score
        elif bet.underdog_id == game.home_id:
            underdog_score = score.home_score
        else:
            raise RuntimeError, "Team/score mismatch game %d" % game.id
        return favored_score, underdog_score
    
    
    def _determine_bet(self, bet_id):
        bet = self.query().get(bet_id)
        if bet is None:
            raise RuntimeError, "Bad bet id %d" % bet_id
        fscore, uscore = self._get_score(bet)
        result = determine_bet(bet, fscore, uscore)
        acct = self.accounts.get(bet.user_id)
        if result == 'push':
            self.accounts.push_bet(acct.id, bet.amount)
        elif result == 'win':
            self.accounts.win_bet(acct.id, bet.amount)
        elif result == 'lose':
            self.accounts.lose_bet(bet.amount)
        else:
            raise RuntimeError, "bad result %s" % result
        

    def get_all_bets(self):
        return self.query().all()
    
    
    
    
