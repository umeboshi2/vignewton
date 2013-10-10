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

