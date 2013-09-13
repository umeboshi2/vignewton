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


team_map = dict(
    arz='Cardinals',
    atl='Falcons',
    bal='Ravens',
    buf='Bills',
    car='Panthers',
    chi='Bears',
    cin='Bengals',
    cle='Browns',
    dal='Cowboys',
    den='Broncos',
    det='Lions',
    grb='Packers',
    hou='Texans',
    ind='Colts',
    jax='Jaguars',
    kcc='Chiefs',
    mia='Dolphins',
    min='Vikings',
    nep='Patriots',
    nos='Saints',
    nyg='Giants',
    nyj='Jets',
    oak='Raiders',
    phl='Eagles',
    pgh='Steelers',
    sdc='Chargers',
    sff='49ers',
    sea='Seahawks',
    stl='Rams',
    tbb='Buccaneers',
    ten='Titans',
    was='Redskins',)

    
class NFLShortTeam(Base):
    __tablename__ = 'vig_nfl_team_map'
    id = Column(Unicode(3), primary_key=True)
    name = Column(Unicode(25), unique=True)
    
    def __init__(self, id, name):
        self.id = id
        self.name = name


def populate_team_map(session):
    with transaction.manager:
        for nick, team in team_map.items():
            shteam = NFLShortTeam(nick, team)
            session.add(shteam)
    

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
