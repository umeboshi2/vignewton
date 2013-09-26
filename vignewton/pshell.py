import urllib2
import csv
import vobject
import os

def make_nfl_team_data(csv_line):
    team, division = csv_line
    name = team.split()[-1].strip()
    city = ' '.join(team.split()[:-1])
    conference, region = division.split()
    return dict(name=name, city=city, conference=conference, region=region)


def more_setup(env):
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
        
    
def even_more_setup(env):
    from vignewton.managers.util import parse_odds_html
    games = parse_odds_html(text)
    env['games'] = games
    from vignewton.managers.nflgames import NFLGameManager
    #from vignewton.models.main import NFLGame
    gm = NFLGameManager(db)
    env['gm'] = gm
    dbgames = [gm.get_game_from_odds(g) for g in games]
    env['dbgames'] = dbgames
    from vignewton.managers.odds import NFLOddsManager
    om = NFLOddsManager(db)
    env['om'] = om
    om.oddscache.set_url(odds_url)
    
    
    
    

def setup(env):
    request = env['request']
    db = request.db
    env['db'] = db
    settings = env['registry'].settings
    
    url = settings['vignewton.nfl.schedule.url']
    env['url'] = url
    env['csv'] = csv
    env['urllib2'] = urllib2
    env['vobject'] = vobject
    #more_setup(env)
    odds_url = settings['vignewton.nfl.odds.url']
    filename = 'odds.html'
    if not os.path.exists(filename):
        with file(filename, 'w') as output:
            r = urllib2.urlopen(odds_url)
            output.writelines(r)
    text = file(filename).read()
    import bs4
    env['b'] = bs4.BeautifulSoup(text, 'lxml')
    from bs4.diagnose import diagnose
    env['diag'] = diagnose
    from vignewton.managers.oddsparser import NewOddsParser
    op = NewOddsParser()
    env['op'] = op
    op.set_html(text)
    from vignewton.managers.nflgames import NFLTeamManager
    tm = NFLTeamManager(db)
    env['tm'] = tm
    from vignewton.managers.odds import NFLOddsManager
    om = NFLOddsManager(db)
    env['om'] = om
    om.oddscache.set_url(odds_url)
    
