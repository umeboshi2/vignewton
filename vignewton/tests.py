import unittest
import transaction

from pyramid import testing

#from .models import DBSession
from vignewton.models.main import DBSession

def initializedb():
    pass

class TestMyView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        from sqlalchemy import create_engine
        engine = create_engine('sqlite://')
        from vignewton.models.main import (
            Base,
            User,
            )
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            model = User('username')
            model.username = "TestUser"
            DBSession.add(model)

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_it(self):
        from vignewton.views.login import LoginViewer
        request = testing.DummyRequest()
        info = LoginViewer(request)
        #self.assertEqual(info['one'].name, 'one')
        #self.assertEqual(info['project'], 'vignewton')
        print info
