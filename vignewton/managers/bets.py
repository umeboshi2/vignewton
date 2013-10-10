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
from vignewton.models.main import CurrentBet, ClosedBet
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

class MinimumBetError(Exception):
    pass

class MaximumBetError(Exception):
    pass

class UnconfirmedBetExistsError(Exception):
    pass

class NoCurrentBetError(Exception):
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
    
        
def make_closed_bet(bet, status, txn):
    now = datetime.now()
    cb = ClosedBet()
    for field in ['id', 'user_id', 'game_id', 'created', 'amount',
                  'bet_type', 'underover', 'team_id', 'total',
                  'spread', 'favored_id', 'underdog_id']:
        value = getattr(bet, field)
        setattr(cb, field, value)
    cb.bet_txn_id = bet.txn_id
    cb.close_txn_id = txn.id
    cb.closed = now
    cb.status = status
    return cb


class BetsManager(object):
    def __init__(self, session):
        self.session = session
        self.games = NFLGameManager(self.session)
        self.teams = NFLTeamManager(self.session)
        self.odds = NFLOddsManager(self.session)
        self.accounts = AccountingManager(self.session)
        # FIXME: put this in config or database
        self.max_bet = 500
        
        
    def query(self):
        return self.session.query(UserBet)

    def get(self, bet_id):
        return self.query().get(bet_id)

    def get_current_bet(self, user_id):
        q = self.session.query(CurrentBet)
        return q.get(user_id)

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
        if amount < 10:
            raise MinimumBetError, "Bet must be at least ten: %d" % amount
        if amount > self.max_bet:
            msg = "Bet must be no more than %d: amount %d"
            raise MaximumBetError, msg % (self.max_bet, amount)
        acct = self.accounts.get(user_id)
        balance = acct.balance.balance
        max_bet = determine_max_bet(balance)
        if amount > max_bet:
            juice_insurance = amount / 10
            total = amount + juice_insurance
            msg = "Total needed %d, current balance %d" % (total, balance)
            raise InsufficientFundsError, msg
        return True

    def check_bet_amount(self, user_id, amount):
        return self._check_amount(user_id, amount)
    
    # pick is either an NFLTeam object, 'over', or 'under'
    def request_bet(self, user_id, game_id, amount, bettype, pick):
        # here we sanitize the bettype and
        # amount arguments
        if bettype not in ['line', 'underover']:
            raise RuntimeError, "Bad bettype %s:" % bettype
        # check amount
        # self.accounts.check_bet_amount(user_id, amount)
        self._check_amount(user_id, amount)
        if self.get_current_bet(user_id) is not None:
            raise UnconfirmedBetExistsError, "Betting in progress"
        with transaction.manager:
            now = datetime.now()
            curbet = CurrentBet()
            curbet.user_id = user_id
            curbet.game_id = game_id
            curbet.created = now
            curbet.amount = amount
            curbet.bet_type = bettype
            if bettype == 'line':
                # the pick is a team
                curbet.team_id = pick.id
            else:
                # the pick is under/over
                curbet.underover = pick
            self.session.add(curbet)
        return self.session.merge(curbet)

    def show_requested_bet(self, user_id):
        current = self.get_current_bet(user_id)
        if current is None:
            raise NoCurrentBetError, "No current bet"
        odds = self._get_odds(current.game_id)
        odata = self.odds.get_data(odds)
        return current, odata
    
    def cancel_requested_bet(self, user_id):
        with transaction.manager:
            q = self.session.query(CurrentBet)
            q = q.filter_by(user_id=user_id)
            q.delete()
            
    def place_requested_bet(self, user_id):
        current, odata = self.show_requested_bet(user_id)
        game_id = current.game_id
        amount = current.amount
        bettype = current.bet_type
        underover = current.underover
        team_id = current.team_id
        account = self.accounts.get(user_id)
        txn = self.accounts.place_bet(account.id, amount)
        with transaction.manager:
            now = datetime.now()
            bet = UserBet()
            bet.user_id = user_id
            bet.game_id = current.game_id
            bet.txn_id = txn.id
            bet.created = current.created
            bet.amount = current.amount
            bet.bet_type = current.bet_type
            bet.underover = current.underover
            bet.team_id = current.team_id
            for field in odata:
                setattr(bet, field, odata[field])
            self.session.add(bet)
            dq = self.session.query(CurrentBet).filter_by(user_id=user_id)
            dq.delete()
        return self.session.merge(bet)
    

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
        if bet.game.score is None:
            return
        fscore, uscore = self._get_score(bet)
        result = determine_bet(bet, fscore, uscore)
        acct = self.accounts.get(bet.user_id)
        if result == 'push':
            txn = self.accounts.push_bet(acct.id, bet.amount)
        elif result == 'win':
            txn = self.accounts.win_bet(acct.id, bet.amount)
        elif result == 'lose':
            txn = self.accounts.lose_bet(bet.amount)
        else:
            raise RuntimeError, "bad result %s" % result
        with transaction.manager:
            cb = make_closed_bet(bet, result, txn)
            self.session.add(cb)
            self.session.delete(bet)
        return self.session.merge(cb)
    
    def determine_bet(self, bet_id):
        return self._determine_bet(bet_id)

    def determine_bets(self):
        closed = list()
        for bet in self.get_all_bets():
            cb = self.determine_bet(bet.id)
            closed.append(cb)
        return closed
    
    def get_all_bets(self):
        return self.query().all()

    def get_all_closed_bets(self):
        return self.session.query(ClosedBet).all()
    
    
    
    
    
