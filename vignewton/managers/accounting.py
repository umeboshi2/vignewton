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

from vignewton.managers.nflgames import NFLGameManager, NFLTeamManager
from vignewton.managers.oddsparser import NFLOddsParser
from vignewton.managers.oddsparser import parse_odds_html

ten_minutes = timedelta(minutes=10)

class AccountingManager(object):
    def __init__(self, session):
        self.session = session

