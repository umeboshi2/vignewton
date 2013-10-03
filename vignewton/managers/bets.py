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


class BetsManager(object):
    def __init__(self, session):
        self.session = session
        self.games = NFLGameManager(self.session)
        self.teams = NFLTeamManager(self.session)
        self.odds = NFLOddsManager(self.session)
        
    def query(self):
        return self.session.query(UserBet)

    def get(self, bet_id):
        return self.query().get(bet_id)
    
