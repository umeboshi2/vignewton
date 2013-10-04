import os
from datetime import datetime, timedelta

import transaction
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import or_

from vignewton.models.nflteamdata import team_map
from vignewton.models.main import NFLGame, NFLTeam
from vignewton.models.main import NFLGameScore, NFLScheduleData
from vignewton.managers.base import BasicCache
from vignewton.managers.util import convert_range_to_datetime
from vignewton.managers.util import parse_nfl_schedule_ical_uid
from vignewton.managers.util import get_nfl_schedule

five_minutes = timedelta(minutes=5)

def parse_ical_nflgame(event):
    uid = unicode(event['uid'])
    away, home = parse_nfl_schedule_ical_uid(uid)
    data = dict(away=away, home=home, uid=uid)
    for f in ['summary', 'description', 'location']:
        data[f] = unicode(event[f])
    for f in ['start', 'end']:
        key = 'dt%s' % f
        data[f] = event[key].dt
    data['class'] = event['class']
    return data


class NFLScheduleCache(BasicCache):
    def __init__(self, session):
        super(NFLScheduleCache, self).__init__(session, NFLScheduleData)

    def set_url(self, url):
        self.url = url

    def latest_schedule(self):
        updated = False
        if self.expired():
            r = requests.get(self.url)
            latest = self.add(r.content)
            updated = True
        else:
            latest = self.get_latest_content()
        return latest, updated
    
    
class NFLTeamManager(object):
    def __init__(self, session):
        self.session = session
        
    def query(self):
        q = self.session.query(NFLTeam)
        return q

    def get(self, id):
        return self.query().get(id)

    def get_by_name(self, name):
        q = self.query()
        q = q.filter_by(name=name)
        return q.one()
    
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
    
    def make_fullname_lookup(self):
        lookup = dict()
        for team in self.all():
            key = '%s %s' % (team.city, team.name)
            key = key.replace('NY', 'New York')
            lookup[key] = team.id
        return lookup
    
    
class NFLGameManager(object):
    def __init__(self, session):
        self.session = session
        self.schedules = NFLScheduleCache(self.session)
        self.teams = NFLTeamManager(self.session)
        self.fnlookup = self.make_fullname_lookup()
        
    def make_fullname_lookup(self):
        return self.teams.make_fullname_lookup()

    def set_schedule_url(self, url):
        self.schedules.set_url(url)

    def get_schedule(self):
        schedule, updated = self.schedules.latest_schedule()
        import icalendar
        cal = icalendar.Calendar.from_ical(bytes)
        events = (e for e in cal.walk() if e.name == 'VEVENT')
        for event in events:
            self.insert_new_game(event)
        
    
        
    def query(self):
        q = self.session.query(NFLGame)
        return q
    
    def get(self, id):
        return self.query().get(id)

    def update_game(self, event):
        data = parse_ical_nflgame(event)
        game = self.get_game_from_ical_event(event, data=data)
        
        
    
    def insert_new_game(self, event):
        data = parse_ical_nflgame(event)
        with transaction.manager:
            g = NFLGame()
            away, home = data['away'], data['home']
            g.away_id = self.teams.getbynick(away).id
            g.home_id = self.teams.getbynick(home).id
            fields = ['summary', 'uid', 'description', 'location',
                      'start', 'end']
            for f in fields:
                setattr(g, f, data[f])
            g.game_class = data['class']
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

    def get_game_from_ical_event(self, event, data=None):
        if data is None:
            data = parse_ical_nflgame(event)
        away_id = self.teams.getbynick(data['away']).id
        home_id = self.teams.getbynick(data['home']).id
        start = data['start']
        q = self.query()
        q = q.filter(func.DATE(NFLGame.start) == start.date())
        q = q.filter(NFLGame.away_id == away_id)
        q = q.filter(NFLGame.home_id == home_id)
        try:
            return q.one()
        except MultipleResultsFound:
            early = gt - five_minutes
            late = gt + five_minutes
            q = q.filter(NFLGame.start >= early)
            q = q.filter(NFLGame.start <= late)
            return q.one()
            
    
    def get_game_from_odds(self, gamedata):
        q = self.query()
        gt = gamedata['gametime']
        away_id = self.fnlookup[gamedata['away']]
        q = q.filter(NFLGame.away_id == away_id)
        # try by date first
        q = q.filter(func.DATE(NFLGame.start) == gt.date())
        try:
            return q.one()
        except MultipleResultsFound:
            early = gt - five_minutes
            late = gt + five_minutes
            q = q.filter(NFLGame.start >= early)
            q = q.filter(NFLGame.start <= late)
            return q.one()
        
    
