from datetime import datetime
from ConfigParser import NoSectionError, DuplicateSectionError

import transaction
from formencode.htmlgen import html
from sqlalchemy.orm.exc import NoResultFound

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import authenticated_userid

from trumpet.security import check_password
from trumpet.security import encrypt_password

from vignewton.managers.admin.users import UserManager
from vignewton.views.base import BaseViewer
from vignewton.views.schema import deferred_choices, make_select_widget

from vignewton.models.base import DBSession
from vignewton.models.usergroup import User, Password
from vignewton.models.usergroup import UserConfig

#########################
#[main]
#sms_email_address = 6015551212@vtext.com
#
#[phonecall_views]
#received = agendaDay
#assigned = agendaWeek
#delegated = agendaWeek
#unread = agendaWeek
#pending = agendaWeek
#closed = month
#
#########################

def get_option(db, user_id, section, option):
    q = db.query(UserOption).filter_by(user_id=user_id)
    q = q.filter_by(section=section).filter_by(option=option)
    return q.one().value

import colander
import deform

class ChangePasswordSchema(colander.Schema):
    oldpass = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5, max=100),
        widget=deform.widget.PasswordWidget(size=20),
        description="Please enter your password.")
    newpass = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5, max=100),
        widget=deform.widget.PasswordWidget(size=20),
        description="Please enter a new password.")
    confirm = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5, max=100),
        widget=deform.widget.PasswordWidget(size=20),
        description="Please confirm the new password.")


#_view_choices = ['agendaDay', 'agendaWeek', 'month']
#ViewChoices = dict(enumerate(_view_choices))
_view_choices = [(0, 'agendaDay'), (1, 'agendaWeek'), (2, 'month')]
ViewChoices = dict(_view_choices)
ViewChoiceLookup = dict([(v, k) for k,v in ViewChoices.items()])

class MainOptionsSchema(colander.Schema):
    sms_email_address = colander.SchemaNode(
        colander.String(),
        title='Cell Phone Email Address',
        )
    

def get_password(request):
    db = request.db
    user_id = request.session['user'].id
    return db.query(Password).filter_by(user_id=user_id).one()
    
def check_old_password(request, password):
    dbpass = get_password(request)
    return check_password(dbpass.password, password)


class MainViewer(BaseViewer):
    def __init__(self, request):
        super(MainViewer, self).__init__(request)
        self.users = UserManager(self.request.db)
        # make default config for user, if needed
        user = self.get_current_user()
        if user.config is None:
            self.users.Make_default_config(user.id)
        self.context = self.request.matchdict['context']
        self.layout.header = "User Preferences"
        self.layout.title = "User Preferences"
        # make left menu
        entries = []
        url = request.route_url('user', context='chpasswd')
        entries.append(('Change Password', url))
        url = request.route_url('user', context='status')
        entries.append(('Status', url))
        menu = self.layout.ctx_menu
        menu.set_new_entries(entries, header='Preferences')
        # make dispatch table
        self._cntxt_meth = dict(
            status=self.status_view,
            chpasswd=self.change_password,
            #mainprefs=self.main_preferences,
            #preferences=self.preferences_view,
            )

        # dispatch context request
        if self.context in self._cntxt_meth:
            self._cntxt_meth[self.context]()
        else:
            msg = 'Undefined Context: %s' % self.context
            self.layout.content = '<b>%s</b>' % msg

    def status_view(self):
        self.layout.content = 'Status View'
        

    def preferences_view(self):
        self.layout.content = "Here are your preferences."

    def main_preferences(self):
        schema = MainOptionsSchema()
        form = deform.Form(schema, buttons=('submit',))
        self.layout.resources.deform_auto_need(form)
        if 'submit' in self.request.POST:
            self._main_pref_form_submitted(form)
        else:
            user = self.get_current_user()
            cfg = user.config.get_config()
            data = dict()
            data['sms_email_address'] = cfg.get('main', 'sms_email_address')
            self.layout.content = form.render(data)

    def _main_pref_form_submitted(self, form):
        db = self.request.db
        controls = self.request.POST.items()
        try:
            data = form.validate(controls)
        except deform.ValidationFailure, e:
            self.layout.content = e.render()
            return
        user = self.get_current_user()
        cfg = user.config.get_config()
        cfg.set('main', 'sms_email_address', data['sms_email_address'])
        user.config.set_config(cfg)
        with transaction.manager:
            db.add(user.config)
                
    def change_password(self):
        schema = ChangePasswordSchema()
        form = deform.Form(schema, buttons=('update',))
        self.layout.resources.deform_auto_need(form)
        if 'update' in self.request.params:
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except deform.ValidationFailure, e:
                self.layout.content = e.render()
                return
            user = self.request.session['user']
            if data['oldpass'] == data['newpass']:
                self.layout.content = "Password Unchanged"
                return
            if data['newpass'] != data['confirm']:
                self.layout.content = "Password Mismatch."
                return
            if check_old_password(self.request, data['oldpass']):
                newpass = data['newpass']
                dbpass = get_password(self.request)
                dbpass.password = encrypt_password(newpass)
                with transaction.manager:
                    self.request.db.add(dbpass)
                self.layout.content = "Password Changed."
                return
            else:
                self.layout.content = "Authentication Failed."
                return
        self.layout.content = form.render()
        
    
        

