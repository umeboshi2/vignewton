from pyramid.security import Allow, Everyone, Authenticated
from fanstatic import Library, Resource
from js.lightbox import lightbox

from haberdashery.resources import jqueryui, fc_css, deform_css



#from trumpet.resources import jqueryui
from trumpet.resources import StaticResources as TrumpetResources

library = Library('vignewton_lib', 'static')
css = Library('vignewton_css', 'static/css')
js = Library('vignewton_js', 'static/js')

favicon = Resource(library, 'favicon.ico')

main_screen = Resource(css, 'mainscreen.css', depends=[deform_css])
admin_screen = Resource(css, 'adminscreen.css', depends=[deform_css])


post_to_url = Resource(js, 'post2url.js', depends=[jqueryui])


main_calendar_view = Resource(js, 'main-calendar-view.js', depends=[fc_css])
main_betgames_view = Resource(js, 'main-betgames-view.js', depends=[jqueryui])


from vignewton.security import authn_policy

class StaticResources(TrumpetResources):
    main_screen = main_screen
    admin_screen = admin_screen
    
    # override trumpet favicon
    favicon = favicon
    

    main_calendar_view = main_calendar_view
    main_betgames_view = main_betgames_view
    
    post_to_url = post_to_url
    lightbox = lightbox
    
    
# the acl entries are allow/deny, group, permission
class RootGroupFactory(object):
    __name__ = ""
    __acl__ = [
        (Allow, Everyone, 'public'),
        (Allow, Authenticated, 'user'),
        (Allow, 'manager', 'manage'),
        (Allow, 'editor', ('wiki_add', 'wiki_edit')),
        (Allow, 'admin', ('admin', 'manage')),
        ]
    authn_policy = authn_policy
    
    def __init__(self, request):
        # comment
        pass

    
