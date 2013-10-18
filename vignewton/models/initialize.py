from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import IntegrityError
from sqlalchemy import engine_from_config

import transaction

from vignewton.models.base import DBSession, Base
from vignewton.models.main import make_test_data

from vignewton.models.usergroup import populate_groups
from vignewton.models.usergroup import populate
from vignewton.models.sitecontent import populate_sitetext
from vignewton.models.main import populate_accounting_tables

from vignewton.managers.nflgames import NFLTeamManager
from vignewton.managers.util import get_nfl_teams_from_string


nfl_team_csv_data = """\
"Team Name","Division"
"Arizona Cardinals  ","NFC West"
"Atlanta Falcons  ","NFC South"
"Baltimore Ravens  ","AFC North"
"Buffalo Bills  ","AFC East"
"Carolina Panthers  ","NFC South"
"Chicago Bears  ","NFC North"
"Cincinnati Bengals  ","AFC North"
"Cleveland Browns  ","AFC North"
"Dallas Cowboys  ","NFC East"
"Denver Broncos  ","AFC West"
"Detroit Lions  ","NFC North"
"Green Bay Packers  ","NFC North"
"Houston Texans  ","AFC South"
"Indianapolis Colts  ","AFC South"
"Jacksonville Jaguars  ","AFC South"
"Kansas City Chiefs  ","AFC West"
"Miami Dolphins  ","AFC East"
"Minnesota Vikings  ","NFC North"
"New England Patriots  ","AFC East"
"New Orleans Saints  ","NFC South"
"NY Giants  ","NFC East"
"NY Jets  ","AFC East"
"Oakland Raiders  ","AFC West"
"Philadelphia Eagles  ","NFC East"
"Pittsburgh Steelers  ","AFC North"
"San Diego Chargers  ","AFC West"
"San Francisco 49ers  ","NFC West"
"Seattle Seahawks  ","NFC West"
"St. Louis Rams  ","NFC West"
"Tampa Bay Buccaneers  ","NFC South"
"Tennessee Titans  ","AFC South"
"Washington Redskins  ","NFC East"
"""




def initialize_database(settings):
    admin_username = settings.get('vignewton.admin.admin_username', 'admin')
    engine = engine_from_config(settings, 'sqlalchemy.')
    Base.metadata.create_all(engine)
    populate_groups()
    populate(admin_username)
    populate_sitetext()
    populate_accounting_tables(DBSession)
    tm = NFLTeamManager(DBSession)
    teams = get_nfl_teams_from_string(nfl_team_csv_data)
    try:
        tm.populate_teams(teams)
    except IntegrityError:
        transaction.abort()
        
