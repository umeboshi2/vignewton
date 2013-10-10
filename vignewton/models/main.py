import transaction

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode, UnicodeText
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Enum
from sqlalchemy import PickleType
from sqlalchemy import Numeric
from sqlalchemy import Boolean

from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError

from vignewton.models.base import Base, DBSession
from vignewton.models.usergroup import User

# these models depend on the Base object above

import vignewton.models.usergroup
import vignewton.models.sitecontent

NFL_CONFERENCE = Enum('AFC', 'NFC', name='vig_nfl_conference')
NFL_REGION = Enum('North', 'South', 'East', 'West', name='vig_nfl_region')

UNDER_OVER = Enum('under', 'over', name='vig_under_over_enum')

BET_TYPE = Enum('underover', 'line')
CLOSED_BET_STATUS = Enum('win', 'lose', 'push', name='vig_closed_bet_status')


class NFLScheduleData(Base):
    __tablename__ = 'vig_nfl_schedule_data'
    id = Column(Integer, primary_key=True)
    retrieved = Column(DateTime, unique=True)
    content = Column(PickleType)
    
class NFLTeam(Base):
    __tablename__ = 'vig_nfl_teams'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    city = Column(Unicode(50))
    conference = Column('conference', NFL_CONFERENCE)
    region = Column('region', NFL_REGION)

    def __repr__(self):
        s = '<NFLTeam: %s %s>' % (self.city, self.name)
        return s
    
    

class NFLGame(Base):
    __tablename__ = 'vig_nfl_games'
    id = Column(Integer, primary_key=True)
    home_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    away_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    uid = Column(Unicode(100), unique=True)
    summary = Column(Unicode(200))
    start = Column(DateTime)
    end = Column(DateTime)
    game_class = Column(Unicode(50))
    description = Column(UnicodeText)
    location = Column(Unicode(100))
    status = Column(Unicode(100))

    def __repr__(self):
        s = '<NFLGame: %s %s>' % (self.summary, self.start.isoformat())
        return s
    
class NFLGameScore(Base):
    __tablename__ = 'vig_nfl_game_scores'
    game_id = Column(Integer,
                     ForeignKey('vig_nfl_games.id'), primary_key=True)
    away_score = Column(Integer)
    home_score = Column(Integer)
    comment = Column(UnicodeText)
    def __repr__(self):
        s = '<NFLGameScore: %d at %d>' % (self.away_score, self.home_score)
        return s


class MainCache(Base):
    __tablename__ = 'vig_main_cache'
    id = Column(Integer, primary_key=True)
    type = Column(Unicode(50))
    retrieved = Column(DateTime)
    updated = Column(DateTime)
    content = Column(PickleType)
    
class NFLOddsData(Base):
    __tablename__ = 'vig_nfl_odds_data'
    id = Column(Integer, primary_key=True)
    retrieved = Column(DateTime, unique=True)
    content = Column(PickleType)

class NFLGameOdds(Base):
    __tablename__ = 'vig_nfl_game_odds'
    game_id = Column(Integer,
                     ForeignKey('vig_nfl_games.id'), primary_key=True)
    retrieved = Column(DateTime, unique=True)
    favored_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    underdog_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    total = Column(Numeric(16,2))
    spread = Column(Numeric(16,2))
    
    
    
NFLGameOdds.game = relationship(NFLGame)
NFLGameOdds.favored = relationship(NFLTeam,
                                   foreign_keys=[NFLGameOdds.favored_id])
NFLGameOdds.underdog = relationship(NFLTeam,
                                   foreign_keys=[NFLGameOdds.underdog_id])

    
NFLGame.away = relationship(NFLTeam,
                            foreign_keys=[NFLGame.away_id])
NFLGame.home = relationship(NFLTeam,
                            foreign_keys=[NFLGame.home_id])

NFLTeam.away_games = relationship(NFLGame,
                                  foreign_keys=[NFLGame.away_id])
NFLTeam.home_games = relationship(NFLGame,
                                  foreign_keys=[NFLGame.home_id])
NFLGame.score = relationship(NFLGameScore, uselist=False, backref='game')


class Account(Base):
    __tablename__ = 'vig_accounts'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), unique=True)

class AccountBalance(Base):
    __tablename__ = 'vig_account_balances'
    account_id = Column(Integer,
                        ForeignKey('vig_accounts.id'), primary_key=True)
    balance = Column(Numeric(16,2))
AccountBalance.account = relationship(Account)

Account.balance = relationship(AccountBalance, uselist=False)

class UserAccount(Base):
    __tablename__ = 'vig_user_accounts'
    account_id = Column(Integer,
                        ForeignKey('vig_accounts.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
UserAccount.user = relationship(User)
UserAccount.account = relationship(Account)

class CurrentBet(Base):
    __tablename__ = 'vig_user_current_bet'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    game_id = Column(Integer,
                     ForeignKey('vig_nfl_games.id'))
    created = Column(DateTime)
    amount = Column(Numeric(16,2))
    bet_type = Column('bet_type', BET_TYPE)
    underover = Column('underover', UNDER_OVER, default='under')
    team_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    
class UserBet(Base):
    __tablename__ = 'vig_user_bets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    game_id = Column(Integer,
                     ForeignKey('vig_nfl_games.id'))
    created = Column(DateTime)
    amount = Column(Numeric(16,2))
    bet_type = Column('bet_type', BET_TYPE)
    underover = Column('underover', UNDER_OVER, default='under')
    team_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    total = Column(Numeric(16,2))
    spread = Column(Numeric(16,2))
    favored_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    underdog_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    
UserBet.game = relationship(NFLGame)
UserBet.favored = relationship(NFLTeam,
                                   foreign_keys=[UserBet.favored_id])
UserBet.underdog = relationship(NFLTeam,
                                   foreign_keys=[UserBet.underdog_id])
UserBet.team = relationship(NFLTeam,
                            foreign_keys=[UserBet.team_id])


class ClosedBet(Base):
    __tablename__ = 'vig_closed_bets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    game_id = Column(Integer,
                     ForeignKey('vig_nfl_games.id'))
    created = Column(DateTime)
    amount = Column(Numeric(16,2))
    bet_type = Column('bet_type', BET_TYPE)
    underover = Column('underover', UNDER_OVER, default='under')
    team_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    total = Column(Numeric(16,2))
    spread = Column(Numeric(16,2))
    favored_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    underdog_id = Column(Integer, ForeignKey('vig_nfl_teams.id'))
    closed = Column(DateTime)
    status = Column('status', CLOSED_BET_STATUS)
    
    
ClosedBet.game = relationship(NFLGame)
ClosedBet.favored = relationship(NFLTeam,
                                   foreign_keys=[ClosedBet.favored_id])
ClosedBet.underdog = relationship(NFLTeam,
                                   foreign_keys=[ClosedBet.underdog_id])
ClosedBet.team = relationship(NFLTeam,
                            foreign_keys=[ClosedBet.team_id])


class BetHistory(Base):
    __tablename__ = 'vig_bets_history'
    id = Column(Integer, primary_key=True)
    bet_id = Column(Integer, ForeignKey('vig_user_bets.id'))

    
class BetStatus(Base):
    __tablename__ = 'vig_bets_board'
    bet_id = Column(Integer, ForeignKey('vig_user_bets.id'), primary_key=True)
    created = Column(DateTime)
    win = Column(Boolean)
    payable = Column(Boolean)
    

class BetFinal(Base):
    __tablename__ = 'vig_bet_finals'
    bet_id = Column(Integer, ForeignKey('vig_user_bets.id'), primary_key=True)
    account_id = Column(Integer, ForeignKey('vig_accounts.id'))
    amount = Column(Numeric(16,2))
    juice = Column(Numeric(16,2))
    created = Column(DateTime)



class TransactionType(Base):
    __tablename__ = 'vig_account_transaction_types'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), unique=True)

class Transaction(Base):
    __tablename__ = 'vig_account_transactions'
    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey('vig_account_transaction_types.id'))
    created = Column(DateTime)

class BaseTransfer(Base):
    __tablename__ = 'vig_account_transfers'
    id = Column(Integer, primary_key=True)
    txn_id = Column(Integer, ForeignKey('vig_account_transactions.id'))
    created = Column(DateTime)
    account_id = Column(Integer, ForeignKey('vig_accounts.id'))
    amount = Column(Numeric(16,2))

BaseTransfer.transaction = relationship(Transaction)
BaseTransfer.account = relationship(Account)


Transaction.transfers = relationship(BaseTransfer)
Transaction.type = relationship(TransactionType)




class Transfer(Base):
    __tablename__ = 'vig_accounting_transfers'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(100), unique=True)


class LedgerEntry(Base):
    __tablename__ = 'vig_accounting_ledger'
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('vig_accounts.id'))
    transfer_id = Column(Integer, ForeignKey('vig_accounting_transfers.id'))
    amount = Column(Numeric(16,2))
    
    
class LoginHistory(Base):
    __tablename__ = 'login_history'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    when = Column(DateTime, primary_key=True)
    

populate = vignewton.models.usergroup.populate

TRANSACTION_TYPES = ['deposit_cash', 'withdraw_cash',
             'deposit_acct', 'withdraw_acct',
             'place_bet', 'win_bet', 'lose_bet',
             'push_bet']


def populate_accounting_tables(session):
    db = session
    try:
        with transaction.manager:
            for ttype in TRANSACTION_TYPES:
                x = TransactionType()
                x.name = ttype
                db.add(x)
    except IntegrityError:
        transaction.abort()
            
    try:
        from vignewton.managers.accounting import AccountingManager
        am = AccountingManager(db)
        for acct in ['Cash', 'Wagers', 'JuiceInsurance', 'InTheWild']:
            am.add_account('%s_Account' % acct)
    except IntegrityError:
        transaction.abort()


def make_test_data(session):
    from vignewton.security import encrypt_password
    from vignewton.models.usergroup import User, Group, UserGroup
    from vignewton.models.usergroup import Password
    db = session
    users = ['thor', 'zeus', 'loki']
    id_count = 1 # admin is already 1
    manager_group_id = 4 # magic number
    # add users
    try:
        with transaction.manager:
            for uname in users:
                id_count += 1
                user = User(uname)
                password = encrypt_password('p22wd')
                db.add(user)
                pw = Password(id_count, password)
                db.add(pw)
                ug = UserGroup(manager_group_id, id_count)
                db.add(ug)
    except IntegrityError:
        transaction.abort()
