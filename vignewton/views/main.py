from datetime import datetime, date, timedelta

from docutils.core import publish_parts

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import authenticated_userid
from pyramid.renderers import render
from pyramid.response import Response

import colander
import deform


from trumpet.views.menus import BaseMenu

from vignewton.views.base import BaseViewer
from vignewton.views.base import make_main_menu, make_ctx_menu

class MainCalJSONViewer(BaseViewer):
    def __init__(self, request):
        super(MainCalJSONViewer, self).__init__(request)
        self.get_everthing()

    def _get_start_end_userid(self, user_id=True):
        start = self.request.GET['start']
        end = self.request.GET['end']
        if user_id:
            user_id = self.request.session['user'].id
        return start, end, user_id
        

    
    def get_everthing(self):
        self.response = []
        
        
    
class MainViewer(BaseViewer):
    def __init__(self, request):
        super(MainViewer, self).__init__(request)
        self.route = self.request.matched_route.name
        self.layout.main_menu = make_main_menu(self.request).render()
        self.layout.ctx_menu = make_ctx_menu(self.request).output()

        # begin dispatch
        if self.route == 'home':
            self.main_view()
            return
        if self.route == 'main':
            self.context = self.request.matchdict['context']
        

        # make dispatch table
        self._cntxt_meth = dict(
            main=self.main_view,
            viewevent=self.view_event,
            viewvenue=self.view_venue,
            viewdayevents=self.view_events_for_day,
            exportevent=self.export_event,
            )

        if self.context in self._cntxt_meth:
            self._cntxt_meth[self.context]()
        else:
            msg = 'Undefined Context: %s' % self.context
            self.layout.content = '<b>%s</b>' % msg

            
    def main_view(self):
        #template = 'goout:templates/main-page.mako'
        #env = dict(dates=dates, dc=dc, dformat=dformat)
        #content = render(template, env, request=self.request)
        content = "Main Page"
        self.layout.content = content
        self.layout.subheader = 'Vig Newton'
        #self.layout.resources.maincalendar.need()
        #self.layout.resources.main_calendar_view.need()
        #self.layout.resources.cornsilk.need()
        
        template = 'vignewton:templates/mainview-calendar.mako'
        env = {}
        content = self.render(template, env)
        self.layout.content = content
        
    def view_event(self):
        pass
    
        
    def export_event(self):
        pass
    
        
    
    def view_venue(self):
        pass

    def view_events_for_day(self):
        pass
    


        


