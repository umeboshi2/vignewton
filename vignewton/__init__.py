import os
from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid_beaker import session_factory_from_settings

from trumpet.config.base import basetemplate, configure_base_layout

from vignewton.security import make_authn_authz_policies, authenticate
from vignewton.models.base import DBSession, Base
from vignewton.config.admin import configure_admin
from vignewton.config.main import configure_wiki

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    # set app name
    appname = 'vignewton'
    # need to use goout root factory for ACL
    root_factory = 'vignewton.resources.RootGroupFactory'
    # alchemy request provides .db method
    request_factory = 'trumpet.request.AlchemyRequest'
    # get admin username
    admin_username = settings.get('vignewton.admin.admin_username', 'admin')
    # create db engine
    engine = engine_from_config(settings, 'sqlalchemy.')
    # setup db.sessionmaker
    settings['db.sessionmaker'] = DBSession
    # bind session to engine
    DBSession.configure(bind=engine)
    # bind objects to engine
    Base.metadata.bind = engine

    if settings.get('db.populate', 'False') == 'True':
        from sqlalchemy.exc import IntegrityError
        from vignewton.models.main import make_test_data
        from vignewton.models.nflteamdata import NFLShortTeam
        Base.metadata.create_all(engine)
        #initialize_sql(engine)
        #make_test_data(DBSession)
        from vignewton.models.usergroup import populate_groups
        populate_groups()
        from vignewton.models.usergroup import populate
        populate(admin_username)
        from vignewton.models.sitecontent import populate_sitetext
        populate_sitetext()

        from vignewton.models.nflteamdata import populate_team_map
        try:
            populate_team_map(DBSession)
        except IntegrityError:
            pass
        
        if os.path.isfile('nfl-teams.csv'):
            from sqlalchemy.exc import IntegrityError
            from vignewton.managers.nflgames import NFLTeamManager
            from vignewton.managers.util import get_nfl_teams
            m = NFLTeamManager(DBSession)
            teams = get_nfl_teams('nfl-teams.csv')
            try:
                m.populate_teams(teams)
            except IntegrityError:
                pass
        
        if os.path.isfile('nfl.ics'):
            from vignewton.managers.nflgames import NFLGameManager
            m = NFLGameManager(DBSession)
            try:
                m.populate_games(file('nfl.ics').read())
            except IntegrityError:
                pass
            
        
    # setup authn and authz
    secret = settings['%s.authn.secret' % appname]
    cookie = settings['%s.authn.cookie' % appname]
    timeout = int(settings['%s.authn.timeout' % appname])
    authn_policy, authz_policy = make_authn_authz_policies(
        secret, cookie, callback=authenticate,
        timeout=timeout)
    # create config object
    config = Configurator(settings=settings,
                          root_factory=root_factory,
                          request_factory=request_factory,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy)
    session_factory = session_factory_from_settings(settings)
    config.set_session_factory(session_factory)

    config.include('pyramid_fanstatic')

    configure_base_layout(config)
    configure_admin(config)
    configure_wiki(config, '/vig_wiki')
    config.add_static_view('static',
                           'vignewton:static', cache_max_age=3600)
    ##################################
    # Main Views
    ##################################
    config.add_route('home', '/')
    config.add_view('vignewton.views.main.MainViewer',
                    layout='base',
                    renderer=basetemplate,
                    route_name='home')
    config.add_route('main', '/main/{context}/{id}')
    config.add_view('vignewton.views.main.MainViewer',
                    layout='base',
                    renderer=basetemplate,
                    route_name='main')
    route_name = 'maincal_json'
    config.add_route(route_name, '/%s/{context}/{id}' % route_name)
    config.add_view('vignewton.views.main.MainCalJSONViewer',
                    route_name=route_name,
                    renderer='json',
                    layout='base',)

    route_name = 'vig_nflteams'
    config.add_route(route_name, '/vignflteams/{context}/{id}')
    config.add_view('vignewton.views.teams.NFLTeamViewer',
                    layout='base',
                    renderer=basetemplate,
                    route_name=route_name)
    ##################################
    # Login Views
    ##################################
    login_viewer = 'vignewton.views.login.LoginViewer'
    config.add_route('login', '/login')
    config.add_view(login_viewer,
                    renderer=basetemplate,
                    layout='base',
                    route_name='login')
    
    
    config.add_route('logout', '/logout')
    config.add_view(login_viewer,
                    renderer=basetemplate,
                    layout='base',
                    route_name='logout')

    
    # Handle HTTPForbidden errors with a
    # redirect to a login page.
    config.add_view(login_viewer,
                    context='pyramid.httpexceptions.HTTPForbidden',
                    renderer=basetemplate,
                    layout='base')
    ##################################

    ##################################
    # Views for Users
    ##################################
    config.add_route('user', '/user/{context}')
    config.add_view('vignewton.views.userview.MainViewer',
                    route_name='user',
                    renderer=basetemplate,
                    layout='base',
                    permission='user')
    
    ##################################
    
    
    # wrap app with Fanstatic
    app = config.make_wsgi_app()
    from fanstatic import Fanstatic
    return Fanstatic(app)

