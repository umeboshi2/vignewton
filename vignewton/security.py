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
    user = dbsession.query(User).get(userid)
    if user is None:
        return None
    else:
        #print "GROUPS--->", user.get_groups()
        groups = user.get_groups()
        if groups is None:
            groups = []
        return groups


def check_user_password(user, password):
    return check_password(user.pw.password, password)


#authn_policy = AuthTktAuthenticationPolicy(
#    secret='v3rys3cret',
#    callback=authenticate)

authn_policy = SessionAuthenticationPolicy(callback=authenticate)
authz_policy = ACLAuthorizationPolicy()


def make_authn_policy(secret, cookie, callback=authenticate,
                      timeout=None):
    ap = AuthTktAuthenticationPolicy(
        secret=secret,
        callback=callback,
        cookie_name=cookie,
        timeout=timeout)
    return ap

def make_session_authn_policy(callback=authenticate):
    sp = SessionAuthenticationPolicy(callback=callback,
                                     )
    return sp


def make_authn_authz_policies(secret, cookie, callback=authenticate,
                              timeout=None, tkt=True):
    if tkt:
        authn_policy = make_authn_policy(secret, cookie, callback, timeout)
    else:
        authn_policy = make_session_authn_policy(callback=callback)
    authz_policy = ACLAuthorizationPolicy()
    return authn_policy, authz_policy


def get_current_user(request):
    user_id = request.session['user'].id
    return request.db.query(User).get(user_id)
