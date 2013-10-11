from trumpet.config.base import basetemplate
from trumpet.config.base import add_view

main_view = 'vignewton.views.admin.main.MainViewer'


def configure_admin(config, rootpath='/admin', permission='admin'):
    config.add_route('admin', rootpath)
    add_view(config, main_view, 'admin', permission=permission)
    config.add_route('admin_images', '%s/images/{context}/{id}' % rootpath)
    add_view(config, 'vignewton.views.admin.images.ImageManagementViewer',
             'admin_images', permission=permission)
    config.add_route('admin_sitetext', '%s/sitetext/{context}/{id}' % rootpath)
    add_view(config, 'vignewton.views.admin.sitetext.SiteTextViewer',
             'admin_sitetext', permission=permission)
    config.add_route('admin_users', '%s/users/{context}/{id}' % rootpath)
    add_view(config, 'vignewton.views.admin.users.UserManagementViewer',
               'admin_users', permission=permission)

    
    config.add_route('admin_credits', '%s/credits/{context}/{id}' % rootpath)
    add_view(config, 'vignewton.views.admin.credits.CreditsViewer',
             'admin_credits', permission=permission)
    
    config.add_route('admin_bets', '%s/bets/{context}/{id}' % rootpath)
    add_view(config, 'vignewton.views.admin.bets.BetsViewer',
             'admin_bets', permission=permission)

    config.add_route('admin_updatedb', '%s/updatedb/{context}/{id}' % rootpath)
    add_view(config, 'vignewton.views.admin.updatedb.UpdateDBViewer',
             'admin_updatedb', permission=permission)
    
