from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import ProgrammingError

from sqlalchemy.orm.exc import NoResultFound

from trumpet.views.base import BaseViewer as TrumpetViewer
from trumpet.views.base import BaseMenu
from trumpet.views.menus import BaseMenu, TopBar

from vignewton.resources import StaticResources
from vignewton.models.usergroup import User
from vignewton.managers.accounting import AccountingManager

def get_admin_username(request):
    skey = 'vignewton.admin.admin_username'
    admin_username = request.registry.settings.get(skey, 'admin')
    return admin_username

def get_user_id(request, username):
    db = request.db
    q = db.query(User).filter_by(username=username)
    return q.one().id

def prepare_layout(layout):
    layout.title = 'Hattiesburg Hustler'
    layout.header = layout.title
    layout.subheader = ''
    layout.content = ''
    layout.ctx_menu = BaseMenu(header=' ')
    layout.footer = ''
    layout.resources = StaticResources()
    layout.resources.favicon.need()


def make_main_menu(request):
    bar = TopBar(request.matched_route.name)
    bar.entries['Home'] = request.route_url('home')
    if 'user' in request.session:
        user = request.session['user']
        if 'admin' in user.groups:
            try:
                url = request.route_url('admin', context='main')
                bar.entries['Admin'] = url
            except KeyError:
                pass
    return bar


def make_ctx_menu(request):
    menu = BaseMenu(header='Main Menu', class_='submenu')
    user = request.session.get('user', None)
    admin_username = get_admin_username(request)
    logged_in = user is not None
    if logged_in:
        #url = request.route_url('user', context='preferences')
        url = request.route_url('user', context='status')
        menu.append_new_entry('Preferences', url)
    else:
        login_url = request.route_url('login')
        menu.append_new_entry('Sign In', login_url)
    if 'user' in request.session:
        user = request.session['user']
    else:
        user = None
    if user is not None:
        if user.username != admin_username:
            url = request.route_url('home')
            menu.append_new_entry('Main View', url)
            url = request.route_url('main',
                                    context='schedcal', id='today')
            menu.append_new_entry('Schedule', url)
            url = request.route_url('vig_betgames',
                                    context='pending', id='bets')
            menu.append_new_entry('My Pending Bets', url)
            url = request.route_url('vig_betgames',
                                    context='closed', id='bets')
            menu.append_new_entry('My Closed Bets', url)
            url = request.route_url('view_wiki')
            menu.append_new_entry('Wiki', url)
            url = request.route_url('vig_nflteams',
                                    context='main', id='all')
            menu.append_new_entry('NFL Teams', url)
        else:
            url = request.route_url('admin', context='main')
            menu.append_new_entry('Admin', url)
    return menu
    
def get_regular_users(request):
    users = request.db.query(User).all()
    skey = 'vignewton.admin.admin_username'
    admin_username = request.registry.settings.get(skey, 'admin')
    return [u for u in users if u.username != admin_username]




class BaseViewer(TrumpetViewer):
    def __init__(self, request):
        super(BaseViewer, self).__init__(request)
        prepare_layout(self.layout)
        self.layout.main_menu = make_main_menu(request).render()
        self.css = self.layout.resources.main_screen
        try:
            self.accounts = AccountingManager(self.request.db)
        except OperationalError:
            self.accounts = None
        except ProgrammingError, e:
            self.layout.header = e

            
    def __call__(self):
        if self.accounts is not None:
            self._update_widgetbox()
        if hasattr(self, 'css'):
            self.css.need()
        return super(BaseViewer, self).__call__()

    def get_current_user_id(self):
        "Get the user id quickly without db query"
        return self.request.session['user'].id

    def get_current_user(self):
        "Get user db object"
        db = self.request.db
        user_id = self.request.session['user'].id
        return db.query(User).get(user_id)

    def get_app_settings(self):
        return self.request.registry.settings

    def get_admin_username(self):
        return get_admin_username(self.request)

    def is_admin_authn(self, authn):
        username = self.get_admin_username()
        user_id = get_user_id(self.request, username)
        return authn == user_id
    
        
        

        
    def _get_account(self):
        try:
            user_id = self.get_current_user_id()
        except KeyError:
            return None
        q = self.accounts.user_account_query()
        q = q.filter_by(user_id=user_id)
        ulist = q.all()
        if not ulist:
            return None
        else:
            return ulist[0].account

    def _update_widgetbox(self):
        account = self._get_account()
        if account is None:
            if 'user' not in self.request.session:
                return
            else:
                template = 'vignewton:templates/admin-widgetbox.mako'
                env = dict(accounts=self.accounts)
        else:
            template = 'vignewton:templates/base-widgetbox.mako'
            env = dict(am=self.accounts, account=account)
        content = self.render(template, env)
        self.layout.widgetbox = content
        
class AdminViewer(BaseViewer):
    def __init__(self, request):
        super(AdminViewer, self).__init__(request)
        self.css = self.layout.resources.admin_screen
        
