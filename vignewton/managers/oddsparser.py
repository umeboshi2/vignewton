import csv
import re
from datetime import datetime, timedelta
import calendar

import requests
import icalendar
import bs4

monthmap = dict(((v,k) for k, v in enumerate([m for m in calendar.month_name])))
AMPM = dict(a='AM', p='PM')

odds_regex_str = r"""in_line\s\(\'(?P<almost>.+(?=,))"""
odds_re = re.compile(odds_regex_str)

game_regex_str = r"""game\s\(\'(?P<date>.+(?=))\',\s\'(?P<time>.+(?=\'))"""
game_re = re.compile(game_regex_str)

game_date_format = '%Y%m%d'
old_game_time_format = '%H:%M'
game_dtformat ='%sT%s' % (game_date_format, old_game_time_format)

two_hours = timedelta(hours=2)

game_time_format = '%I:%M %p'


team_markers = {
    "ARIZONA":"Cardinals",
    "ATLANTA":"Falcons",
    "BALTIMORE":"Ravens",
    "BUFFALO":"Bills",
    "CAROLINA":"Panthers",
    "CHICAGO":"Bears",
    "CINCINNATI":"Bengals",
    "CLEVELAND":"Browns",
    "DALLAS":"Cowboys",
    "DENVER":"Broncos",
    "DETROIT":"Lions",
    "GREEN BAY":"Packers",
    "HOUSTON":"Texans",
    "INDIANAPOLIS":"Colts",
    "JACKSONVILLE":"Jaguars",
    "KANSAS CITY":"Chiefs",
    "MIAMI":"Dolphins",
    "MINNESOTA":"Vikings",
    "NEW ENGLAND":"Patriots",
    "NEW ORLEANS":"Saints",
    "NY GIANTS":"Giants",
    "NY JETS":"Jets",
    "OAKLAND":"Raiders",
    "PHILADELPHIA":"Eagles",
    "PITTSBURGH":"Steelers",
    "SAN DIEGO":"Chargers",
    "SAN FRANCISCO":"49ers",
    "SEATTLE":"Seahawks",
    "ST. LOUIS":"Rams",
    "TAMPA BAY":"Buccaneers",
    "BUCS":"Buccaneers",
    "TENNESSEE":"Titans",
    "WASHINGTON":"Redskins",
    }


def parse_game_time(datestring, timestring):
    now = datetime.now()
    dtstring = '%sT%s' % (datestring, timestring)
    gametime = now.strptime(dtstring, game_dtformat) + two_hours
    return gametime

    


class BDNFLOddsParser(object):
    def __init__(self):
        self.games = list()
        self.current_game = None
        self.events = list()

    

    

class DSNFLOddsParser(object):
    def __init__(self):
        self.lines = list()
        self.games = list()
        self.current_game = None
        self.events = list()
        
    def set_text(self, text):
        self.lines = [l.strip() for l in text.split('\r\n') if l.strip()]
        self.games = list()
        self.current_game = None
        self.ignore_in_game_odds = False
        self.events = list()
        
    def parse(self):
        while self.lines:
            line = self.lines.pop(0)
            self._main_handle_line(line)
            

    def _find_team(self, line):
        team = None
        for city in team_markers:
            if city in line:
                team = team_markers[city]
                break
            if team_markers[city].upper() in line:
                team = team_markers[city]
                break
        if team is None:
            raise RuntimeError, "No team found for %s" % line
        return team


    def _main_handle_line(self, line):
        if line.startswith('end_game'):
            self._handle_end_game(line)
        elif line.startswith('in_team'):
            self._handle_in_team(line)
        elif line.startswith('in_game'):
            self._handle_start_game(line)
        elif line.startswith('in_line'):
            self._handle_in_line(line)
        elif line.startswith('print_header'):
            self._handle_print_header(line)
        elif line.startswith('number_of_books'):
            self.lines = list()
        elif line.startswith('league ='):
            pass
        elif line.startswith('put_name'):
            pass
        
        else:
            raise RuntimeError , "Unhandled line %s" % line
        
            

            
    def _handle_start_game(self, line):
        if self.ignore_in_game_odds:
            return
        self.current_game = dict()
        #self.current_game['gameline'] = line
        search = game_re.search(line)
        if search is not None:
            data = search.groupdict()
            self.current_game['game'] = parse_game_time(
                data['date'], data['time'])
        else:
            self.events.append("BAD GAME LINE-> %s" % line)
            import pdb ; pdb.set_trace()
            
    def _handle_end_game(self, line):
        if self.ignore_in_game_odds:
            return
        self.games.append(self.current_game)
        self.current_game = None
    
    def _handle_in_team(self, line):
        if self.ignore_in_game_odds:
            return
        team = self._find_team(line)
        if 'favored' in self.current_game:
            self.current_game['underdog'] = team
        else:
            self.current_game['favored'] = team
            

    def _handle_in_line(self, line):
        if self.ignore_in_game_odds:
            return
        if 'underdog' in self.current_game:
            key = 'underdog_odds'
        else:
            key = 'favored_odds'
        if key not in self.current_game:
            match = odds_re.match(line)
            value = match.groupdict()['almost']
            if value.endswith("'"):
                value = value[:-1]
            self.current_game[key] = value
            
            

    def _handle_print_header(self, line):
        if 'NFL FUTURES' in line:
            self.lines = list()
        if 'NFL IN-GAME LINES' in line:
            self.ignore_in_game_odds = True
            self.events.append('Ignoring line %s' % line)
        if 'NFL WEEK' in line:
            self.events.append('GAMES line %s' % line)
            self.ignore_in_game_odds = False
            
    


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
        gametime = datetime.combine(d, t) + two_hours
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

