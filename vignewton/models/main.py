import transaction

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode, UnicodeText
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Enum


from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError

from vignewton.models.base import Base, DBSession

# these models depend on the Base object above

import vignewton.models.usergroup
import vignewton.models.sitecontent

NFL_CONFERENCE = Enum('AFC', 'NFC', name='vig_nfl_conference')
NFL_REGION = Enum('North', 'South', 'East', 'West', name='vig_nfl_region')


class NFLTeam(Base):
    __tablename__ = 'vig_nfl_teams'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    city = Column(Unicode(50))
    conference = Column('conference', NFL_CONFERENCE)
    region = Column('region', NFL_REGION)
    
    

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

NFLGame.away = relationship(NFLTeam,
                            foreign_keys=[NFLGame.away_id])
NFLGame.home = relationship(NFLTeam,
                            foreign_keys=[NFLGame.home_id])

NFLTeam.away_games = relationship(NFLGame,
                                  foreign_keys=[NFLGame.away_id])
NFLTeam.home_games = relationship(NFLGame,
                                  foreign_keys=[NFLGame.home_id])


class UserBalance(Base):
    __tablename__ = 'vig_nfl_games'


#class NFLBet(Base):
#    pass

class LoginHistory(Base):
    __tablename__ = 'login_history'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    when = Column(DateTime, primary_key=True)
    

populate = vignewton.models.usergroup.populate




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
