import os
from datetime import datetime, timedelta

import transaction
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import or_

from vignewton.models.nflteamdata import team_map
from vignewton.models.main import NFLGame, NFLTeam
from vignewton.managers.util import convert_range_to_datetime
from vignewton.managers.util import parse_nfl_schedule_ical_uid

class NFLTeamManager(object):
    def __init__(self, session):
        self.session = session
        
    def query(self):
        q = self.session.query(NFLTeam)
        return q

    def get(self, id):
        return self.query().get(id)

    def getbynick(self, nick):
        name = team_map[nick]
        q = self.query()
        q = q.filter(NFLTeam.name == name)
        return q.one()

    def all(self):
        return self.query().all()
    

    def add_team(self, teamdata):
        with transaction.manager:
            team = NFLTeam()
            for field, value in teamdata.items():
                setattr(team, field, value)
            self.session.add(team)
        return self.session.merge(team)

    def populate_teams(self, teams):
        with transaction.manager:
            for teamdata in teams:
                team = NFLTeam()
                for field, value in teamdata.items():
                    setattr(team, field, value)
                self.session.add(team)
    
    def get_all_games(self, team_id):
        with transaction.manager:
            q = self.session.query(NFLGame)
            q = q.filter(or_(NFLGame.home_id == team_id,
                             NFLGame.away_id == team_id))
            q = q.order_by(NFLGame.start)
            games = q.all()
        return games
    
                    
class NFLGameManager(object):
    def __init__(self, session):
        self.session = session
        self.teams = NFLTeamManager(self.session)
        
    def query(self):
        q = self.session.query(NFLGame)
        return q
    
    def get(self, id):
        return self.query().get(id)

    def insert_new_game(self, event):
        with transaction.manager:
            g = NFLGame()
            away, home = parse_nfl_schedule_ical_uid(unicode(event['uid']))
            g.away_id = self.teams.getbynick(away).id
            g.home_id = self.teams.getbynick(home).id
            for field in ['summary', 'uid', 'description', 'location']:
                setattr(g, field, unicode(event[field]))
            for field in ['start', 'end']:
                key = 'dt%s' % field
                setattr(g, field, event[key].dt)
            g.game_class = event['class']
            self.session.add(g)
        return self.session.merge(g)
        

    def _range_filter(self, query, start, end):
        query = query.filter(NFLGame.start >= start)
        query = query.filter(NFLGame.start <= end)
        return query
    
    def get_games(self, start, end, timestamps=False):
        if timestamps:
            start, end = convert_range_to_datetime(start, end)
        q = self.query()
        q = self._range_filter(q, start, end)
        return q.all()

    def populate_games(self, bytes):
        import icalendar
        cal = icalendar.Calendar.from_ical(bytes)
        events = (e for e in cal.walk() if e.name == 'VEVENT')
        for event in events:
            self.insert_new_game(event)
            
    
