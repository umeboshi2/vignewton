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
    #from vignewton.models.main import NFLGame
    gm = NFLGameManager(db)
    env['gm'] = gm
    dbgames = [gm.get_game_from_odds(g) for g in games]
    env['dbgames'] = dbgames
    from vignewton.managers.odds import NFLOddsManager
    om = NFLOddsManager(db)
    env['om'] = om
    om.oddscache.set_url(odds_url)
    
    
    
    
def backup_cache(gm, om):
    ofilename = 'odds-cache.zip'
    sfilename = 'sched-cache.zip'
    with file(ofilename, 'wb') as o:
        o.write(om.archive_cache_table())
    with file(sfilename, 'wb') as o:
        o.write(gm.archive_cache_table())
def update_games(gm):
    filename = 'testdata/s2.pickle'
    gm.update_from_pickle(filename)

def setup(env):
    request = env['request']
    db = request.db
    env['db'] = db
    settings = env['registry'].settings
    
    url = settings['vignewton.nfl.schedule.url']
    env['url'] = url
    odds_url = settings['vignewton.nfl.odds.url']
    from vignewton.managers.nflgames import NFLTeamManager
    tm = NFLTeamManager(db)
    env['tm'] = tm
    from vignewton.managers.odds import NFLOddsManager
    om = NFLOddsManager(db)
    env['om'] = om
    om.oddscache.set_url(odds_url)
    if not om.get_current_odds():
        filename = 'testdata/o.pickle'
        if not os.path.isfile(filename):
            om.update_current_odds()
        else:
            om.populate_from_pickle(filename)
    from vignewton.managers.nflgames import NFLGameManager
    gm = NFLGameManager(db)
    env['gm'] = gm
    gm.set_schedule_url(url)
    update_game_schedule = False
    if update_game_schedule:
        update_games(gm)
    env['ug'] = update_games
    from vignewton.managers.accounting import AccountingManager
    am = AccountingManager(db)
    am.initialize_bets_manager()
    env['am'] = am
    #env['games'] = om.oddscache.get_latest()[0].content
    #env['bg'] = env['games'][-3]
    from vignewton.managers.util import determine_max_bet
    env['dmb'] = determine_max_bet
    env['game'] = gm.query().get(125)
    backup_cache(gm, om)
    from vignewton.managers.bets import BetsManager
    bm = BetsManager(db)
    env['bm'] = bm
    
    
