import os
from datetime import datetime, timedelta

import transaction
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import desc
from sqlalchemy import func

from vignewton.models.main import NFLGame
from vignewton.managers.util import convert_range_to_datetime

class NFLGameManager(object):
    def __init__(self, session):
        self.session = session
        
    def query(self):
        q = self.session.query(NFLGame)
        return q
    
    def get(self, id):
        return self.query().get(id)

    def insert_new_game(self, event):
        with transaction.manager:
            g = NFLGame()
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
            
