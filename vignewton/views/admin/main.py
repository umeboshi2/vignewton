from cStringIO import StringIO
from datetime import datetime

import transaction
from PIL import Image

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import authenticated_userid
from pyramid.renderers import render

from trumpet.models.base import DBSession
from trumpet.models.sitecontent import SiteImage

from trumpet.views.base import NotFound
#from trumpet.views.base import BaseViewer, make_main_menu
from trumpet.views.menus import BaseMenu

import colander
import deform


from vignewton.managers.nflgames import NFLGameManager
from vignewton.managers.odds import NFLOddsManager
from vignewton.managers.bets import BetsManager

from vignewton.views.base import AdminViewer, make_main_menu


def prepare_main_data(request):
    layout = request.layout_manager.layout
    menu = layout.ctx_menu
    url = request.route_url('admin_users', context='list', id='all')
    menu.append_new_entry('Manage Users', url)
    url = request.route_url('admin_credits', context='main', id=None)
    menu.append_new_entry('Manage Credits', url)
    url = request.route_url('admin_bets', context='main', id='all')
    menu.append_new_entry('View Betting', url)
    url = request.route_url('admin_updatedb', context='main', id='db')
    menu.append_new_entry('Update Database', url)
    url = request.route_url('admin_sitetext', context='list', id=None)
    menu.append_new_entry('Manage Text', url)
    url = request.route_url('admin_images', context='list', id=None)
    menu.append_new_entry('Manage Images', url)
    url = request.route_url('user', context='status')
    menu.append_new_entry('Preferences', url)
    main_menu = make_main_menu(request)
    layout.title = 'Admin Page'
    layout.header = 'Admin Page'
    layout.main_menu = main_menu.render()
    layout.ctx_menu = menu


class MainViewer(AdminViewer):
    def __init__(self, request):
        super(MainViewer, self).__init__(request)
        prepare_main_data(request)
        
        self.games = NFLGameManager(self.request.db)
        self.odds = NFLOddsManager(self.request.db)
        self.bets = BetsManager(self.request.db)
        
        template = 'vignewton:templates/admin-main-view.mako'
        env = dict(odds=self.odds, games=self.games, bets=self.bets)
        content = self.render(template, env)
        self.layout.content = content
        
