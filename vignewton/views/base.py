from trumpet.views.base import BaseViewer as TrumpetViewer
from trumpet.views.base import BaseMenu
from trumpet.views.menus import BaseMenu, TopBar

from vignewton.resources import StaticResources
from vignewton.models.usergroup import User

def prepare_layout(layout):
    layout.title = 'Vig Newton'
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
        url = request.route_url('view_wiki')
        menu.append_new_entry('Wiki', url)
        
    return menu
    
class BaseViewer(TrumpetViewer):
    def __init__(self, request):
        super(BaseViewer, self).__init__(request)
        prepare_layout(self.layout)
        self.layout.main_menu = make_main_menu(request).render()
        self.css = self.layout.resources.main_screen
        
    def __call__(self):
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
    
class AdminViewer(BaseViewer):
    def __init__(self, request):
        super(AdminViewer, self).__init__(request)
        self.css = self.layout.resources.admin_screen
        
