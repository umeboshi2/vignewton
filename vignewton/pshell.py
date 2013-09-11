import urllib2
import csv
import vobject

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
    env['stream'] = file(filename).read()
    
