import csv
import re
from datetime import datetime, timedelta
import calendar

import requests
import icalendar
import bs4

monthmap = dict(((v,k) for k, v in enumerate([m for m in calendar.month_name])))
AMPM = dict(a='AM', p='PM')

one_hour = timedelta(hours=1)
two_hours = timedelta(hours=2)

game_time_format = '%I:%M %p'


class NewOddsParser(object):
    def __init__(self):
        self.text = None
        self.soup = None

    def set_html(self, html):
        self.text = html
        self.soup = bs4.BeautifulSoup(self.text, 'lxml')
        self.days = dict()
        self.current_date = None
        self.games = list()
        
    def _select_one(self, element, selector):
        elist = element.select(selector)
        if len(elist) > 1:
            raise RuntimeError, "Too many %s" % selector
        if elist:
            return elist.pop()
        

    def get_event_schedule(self):
        return self._select_one(self.soup, '#event-schedule')

    def handle_event(self, event):
        gdate = self.current_date
        head, body = event.children
        gtime, ampm = head.next.text.split()
        gtimestr = '%s %s' % (gtime, AMPM[ampm])
        gtime = datetime.strptime(gtimestr, game_time_format)
        d = gdate.date()
        t = gtime.time()
        gametime = datetime.combine(d, t) - one_hour
        away_tr = self._select_one(body, '.away')

        competitor = self._select_one(away_tr, '.competitor-name')
        away_name = competitor.next.text

        runline_td = self._select_one(away_tr, '.runline')
        away_runline = ''.join(runline_td.next.text.split())
        
        totalnumber_div = self._select_one(away_tr, '.total-number')
        totalnumber = totalnumber_div.next.text

        home_tr = self._select_one(body, '.home')

        competitor = self._select_one(home_tr, '.competitor-name')
        home_name = competitor.next.text

        runline_td = self._select_one(home_tr, '.runline')
        home_runline = ''.join(runline_td.next.text.split())
        data = dict(gametime=gametime, home=home_name, away=away_name,
                    home_line=home_runline, away_line=away_runline,
                    total=totalnumber)
        self.days[gdate].append(data)
        self.games.append(data)
    
    def handle_event_schedule_child(self, child):
        if 'class' in child.attrs and child['class'] == ['schedule-date']:
            date = self.get_date(child)
            self.days[date] = []
            self.current_date = date
        elif 'class' in child.attrs and child['class'] == ['event']:
            self.handle_event(child)
            
        
        
    def handle_event_schedule(self, event_schedule):
        es = event_schedule
        children = es.children
        for child in children:
            self.handle_event_schedule_child(child)
            
    def get_days(self, event_schedule):
        return event_schedule.select('.schedule-date')

    def get_date(self, day):
        now = datetime.now()
        m, d = day.next.text.split()
        d = int(d)
        m = monthmap[m.capitalize()]
        year = now.year
        if m < now.month:
            year = now.year +1
        date = datetime(year, m, d)
        return date

    def parse(self):
        es = self.get_event_schedule()
        self.handle_event_schedule(es)
        
        
    
        

    
                     
        
            
def parse_odds_html(odds_html):
    b = bs4.BeautifulSoup(odds_html)
    scripts = b.find_all('script')
    parser = NFLOddsParser()
    all_games = list()
    for s in scripts:
        parser.set_text(s.text)
        parser.parse()
        all_games += parser.games
    return all_games

