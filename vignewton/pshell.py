import urllib2
import csv
import vobject

def make_nfl_team_data(csv_line):
    team, division = csv_line
    name = team.split()[-1].strip()
    city = ' '.join(team.split()[:-1])
    conference, region = division.split()
    return dict(name=name, city=city, conference=conference, region=region)
    

def setup(env):
    db = env['request'].db
    env['db'] = db
    url = env['registry'].settings['vignewton.nfl.schedule.url']
    env['url'] = url
    env['csv'] = csv
    env['urllib2'] = urllib2
    env['vobject'] = vobject
    import os
    filename = 'nfl.ics'
    if not os.path.exists(filename):
        with file(filename, 'w') as output:
            r = urllib2.urlopen(url)
            output.write(r.read())
    cfile = file(filename)
    stream = file(filename).read()
    import icalendar
    cal = icalendar.Calendar.from_ical(stream)
    events = (e for e in cal.walk() if e.name == 'VEVENT')
    env['cal'] = cal
    env['events'] = events
    teamfilename = 'nfl-teams.csv'
    url = env['registry'].settings['vignewton.nfl.teams.url']
    if not os.path.exists(teamfilename):
        with file(teamfilename, 'w') as output:
            r = urllib2.urlopen(url)
            output.write(r.read())
        
    
