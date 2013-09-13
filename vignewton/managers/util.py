import csv
from datetime import datetime

import requests
import icalendar


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

def get_nfl_odds(url):
    r = requests.get(url)
    

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

    
