import csv
import re
from datetime import datetime, timedelta

import requests
import icalendar
import bs4



class GameDateCollector(object):
    def __init__(self, games):
        self.gdates = dict()
        for game in games:
            self._add_game(game)
            
    def _add_game(self, game):
        dt = game.start
        date = dt.date()
        try:
            self.gdates[date].append(game)
        except KeyError:
            self.gdates[date] = [game]

    @property
    def dates(self):
        return self.gdates

class BettableGamesCollector(object):
    def __init__(self, olist):
        self.gdates = dict()
        for odds in olist:
            self._add_game(odds)

    def _add_game(self, odds):
        date = odds.game.start.date()
        try:
            self.gdates[date].append(odds)
        except KeyError:
            self.gdates[date] = [odds]
        
    @property
    def dates(self):
        return self.gdates
    
def parse_game_time(datestring, timestring):
    now = datetime.now()
    dtstring = '%sT%s' % (datestring, timestring)
    gametime = now.strptime(dtstring, game_dtformat) + two_hours
    return gametime

    

def download_url(url, filename=None):
    r = requests.get(url)
    if filename is not None:
        with file(filename, 'w') as output:
            output.write(r.text)
    else:
        return r.text
    

def convert_range_to_datetime(start, end):
    "start and end are timestamps"
    start = datetime.fromtimestamp(float(start))
    end = datetime.fromtimestamp(float(end))
    return start, end
    

def make_nfl_team_data(csv_line):
    team, division = csv_line
    name = team.split()[-1].strip()
    city = ' '.join(team.split()[:-1])
    conference, region = division.split()
    return dict(name=name, city=city, conference=conference, region=region)

def get_nfl_teams(filename):
    teams = csv.reader(file(filename))
    ignore = teams.next()
    teamdata = list()
    for line in teams:
        teamdata.append(make_nfl_team_data(line))
    return teamdata




def get_nfl_schedule(filename=None, url=None):
    if filename is None and url is None:
        raise RuntimeError, "We need a keyword argument"
    text = None
    if url is not None:
        text = download_url(url)
        # if both filename and url are used, we save to file
        if filename is not None:
            with file(filename, 'w') as output:
                output.write(text)
            return
    else:
        text = file(filename).read()


def parse_nfl_schedule_ical_uid(uid):
    away = uid[7:10].lower()
    home = uid[10:13].lower()
    return away, home

def parse_nfl_schedule_ical_summary(summary):
    scores = False
    if ' at ' in summary:
        #print "SUMMARY", summary
        try:
            # we put the spaces around at to keep from
            # crashing in Cincinnati
            away, home = summary.split(' at ')
        except ValueError:
            import pdb
            pdb.set_trace()
    else:
        return scores, None, None
    away_score = away.split()[-1]
    if not away_score.isdigit():
        return scores, None, None
    home_score = home.split()[-1]
    if not home_score.isdigit():
        return scores, None, None
    scores = True
    return scores, int(away_score), int(home_score)


def chop_ical_nflgame_desc(desc):
    lines = desc.split('\n')[:2]
    lines = [l.strip() for l in lines if l.strip()]
    #return lines
    return ''.join([l + '\n' for l in lines])



def parse_ical_nflgame(event):
    uid = unicode(event['uid'])
    away, home = parse_nfl_schedule_ical_uid(uid)
    data = dict(away=away, home=home, uid=uid)
    for f in ['summary', 'location']:
        data[f] = unicode(event[f])
    for f in ['start', 'end']:
        key = 'dt%s' % f
        data[f] = event[key].dt
    d = unicode(chop_ical_nflgame_desc(event['description']))
    data['description'] = d
    data['class'] = event['class']
    data['scores'] = parse_nfl_schedule_ical_summary(data['summary'])
    return data

def parse_ical_nflschedule(content):
    cal = icalendar.Calendar.from_ical(content)
    return (e for e in cal.walk() if e.name == 'VEVENT')

def determine_max_bet(balance):
    balance = int(balance)
    juice_money = balance / 10
    workable = balance - juice_money
    workable_tens = workable / 10
    true_workable = workable_tens * 10
    if true_workable + juice_money > balance:
        raise RuntimeError, "Big problem with math"
    return true_workable
