import os
import random
import requests
from twill import get_browser



SITE = 'http://paperboy:6542/'

login_url = os.path.join(SITE, 'login')
logout_url = os.path.join(SITE, 'logout')
admin_prefix = os.path.join(SITE, 'admin')
credits_prefix = os.path.join(admin_prefix, 'credits')
adduser_url = os.path.join(admin_prefix, 'users/add/somebody')

deposit_cash_url = os.path.join(credits_prefix, 'cashdeposit/cash')
withdraw_cash_url = os.path.join(credits_prefix, 'cashwithdraw/cash')
deposit_acct_url = os.path.join(credits_prefix, 'acctdeposit/somebody')
withdraw_acct_url = os.path.join(credits_prefix, 'acctwithdraw/somebody')

betgame_prefix = os.path.join(SITE, 'vigbetgames')
confirm_url = os.path.join(betgame_prefix, 'confirmbet/bet')
cancel_url = os.path.join(betgame_prefix, 'cancelbet/bet')
                                
def logout(browser):
    url = os.path.join(SITE, 'logout')
    browser.go(url)

 

def login_as_admin(browser):
    url = os.path.join(SITE, 'login')
    browser.go(url)
    form = browser.get_form(1)
    for field in ['username', 'password']:
        form.set_value('admin', field)
    browser.submit()
    browser.save_cookies('admin.cookies')

def login(browser, username, password):
    filename = '%s.cookies' % username
    if os.path.isfile(filename):
        browser.load_cookies(filename)
    url = os.path.join(SITE, 'login')
    browser.go(url)
    form = browser.get_form(1)
    form.set_value(username, 'username')
    form.set_value(password, 'password')
    browser.submit()
    browser.save_cookies(filename)
    
def add_user(browser, name, password):
    browser.go(adduser_url)
    form = browser.get_form(1)
    form.set_value(name, 'name')
    for field in ['password', 'confirm']:
        form.set_value(password, field)
    browser.submit()
    

def deposit_cash(browser, amount):
    browser.go(deposit_cash_url)
    form = browser.get_form(1)
    form.set_value(str(amount), 'amount')
    browser.submit()
    

def withdraw_cash(browser, amount):
    browser.go(withdraw_cash_url)
    form = browser.get_form(1)
    form.set_value(str(amount), 'amount')
    browser.submit()


def deposit_acct(browser, user_id, amount):
    browser.go(deposit_acct_url)
    form = browser.get_form(1)
    form.set_value([str(user_id)], 'user')
    form.set_value(str(amount), 'amount')
    browser.submit()

def withdraw_acct(browser, user_id, amount):
    browser.go(withdraw_acct_url)
    form = browser.get_form(1)
    form.set_value([str(user_id)], 'user')
    form.set_value(str(amount), 'amount')
    browser.submit()

def make_bet_url(type, game_id):
    context = 'bet%s' % type
    suffix = '%s/%d' % (context, game_id)
    return os.path.join(betgame_prefix, suffix)

def make_bet(browser, game_id, type, amount):
    url = make_bet_url(type, game_id)
    browser.go(url)
    a = '$%03d' % amount
    form = browser.get_form(1)
    form.set_value(a, 'amount')
    browser.submit()
    browser.go(confirm_url)
    
def make_random_bets(count=None):
    if count is None:
        count = 10
    games = range(131, 142)
    types = ['favored', 'underdog', 'under', 'over']
    amounts = [10*i for i in range(1, 5)]
    users = ['al', 'bob', 'carol', 'dave']
    #make_bet(albrowser, 131, 'favored', 20)
    for bet in range(count):
        user = random.choice(users)
        browser = get_browser()
        login(browser, user, 'p22wd')
        game = random.choice(games)
        type = random.choice(types)
        amount = random.choice(amounts)
        make_bet(browser, game, type, amount)
        
    
PGUSERS = dict(al=3, bob=4, carol=5, dave=6)
SQLITEUSERS = dict(al=2, bob=3, carol=4, dave=5)
USERS = PGUSERS

        
if __name__ == "__main__":
    admin = get_browser()
    if os.path.isfile('admin.cookies'):
        admin.load_cookies('admin.cookies')
    login_as_admin(admin)
    init = True
    if init:
        add_user(admin, 'al', 'p22wd')
        add_user(admin, 'bob', 'p22wd')
        add_user(admin, 'carol', 'p22wd')
        add_user(admin, 'dave', 'p22wd')
        
        deposit_cash(admin, 2500)
        for user in USERS:
            uid = USERS[user]
            amount = 100 * uid
            deposit_acct(admin, uid, amount)
    #a = get_browser()
    #login(a, 'al', 'p22wd')
    #b = get_browser()
    #login(b, 'bob', 'p22wd')
    #c = get_browser()
    #login(c, 'carol', 'p22wd')
    #d = get_browser()
    #login(d, 'dave', 'p22wd')

    make_random_bets(50)
