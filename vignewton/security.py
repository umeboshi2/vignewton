from crypt import crypt
import random
from string import ascii_letters

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authentication import SessionAuthenticationPolicy

from pyramid.authorization import ACLAuthorizationPolicy
from sqlalchemy.orm.exc import NoResultFound

from vignewton.models.usergroup import User, Password


def make_salt(id=5, length=10):
    phrase = ''
    for ignore in range(length):
        phrase += random.choice(ascii_letters)
    return '$%d$%s$' % (id, phrase)


def encrypt_password(password):
    salt = make_salt()
    encrypted = crypt(password, salt)
    return encrypted


def check_password(encrypted, password):
    if '$' not in encrypted:
        raise RuntimeError("we are supposed to be using random salt.")
    ignore, id, salt, epass = encrypted.split('$')
    salt = '$%s$%s$' % (id, salt)
    check = crypt(password, salt)
    return check == encrypted


def authenticate(userid, request):
    #print "called authenticate", request.params
    dbsession = request.db
    user = None
    try:
        user = dbsession.query(User).filter_by(username=userid).one()
    except NoResultFound:
        pass
    if user is None:
        pass
    else:
        #print "GROUPS--->", user.get_groups()
        return user.get_groups()


def check_user_password(user, password):
    return check_password(user.pw.password, password)


#authn_policy = AuthTktAuthenticationPolicy(
#    secret='v3rys3cret',
#    callback=authenticate)

authn_policy = SessionAuthenticationPolicy(callback=authenticate)
authz_policy = ACLAuthorizationPolicy()


def make_authn_authz_policies(secret, cookie, callback=authenticate,
                              timeout=None):
    authn_policy = AuthTktAuthenticationPolicy(
        secret=secret,
        callback=callback,
        cookie_name=cookie,
        timeout=timeout)
    authn_policy = SessionAuthenticationPolicy(callback=authenticate)
    authz_policy = ACLAuthorizationPolicy()
    return authn_policy, authz_policy


def get_current_user(request):
    user_id = request.session['user'].id
    return request.db.query(User).get(user_id)
