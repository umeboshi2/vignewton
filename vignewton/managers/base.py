import os
from datetime import datetime, timedelta

import transaction
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import or_


five_minutes = timedelta(minutes=5)

class BasicCache(object):
    def __init__(self, session, dbmodel):
        self.session = session
        self.dbmodel = dbmodel
        self.ttl = five_minutes

    def set_ttl(self, **kw):
        self.ttl = timedelta(**kw)
        
    def query(self):
        return self.session.query(self.dbmodel)

    def get(self, id):
        return self.query().get(id)

    def get_latest_content(self):
        q = self.query()
        q = q.order_by(self.dbmodel.retrieved.desc())
        return q.first()

    def expired(self):
        now = datetime.now()
        latest = self.get_latest_content()
        return latest is None or now - latest.retrieved >= self.ttl

    def add(self, content):
        with transaction.manager:
            now = datetime.now()
            data = self.dbmodel()
            data.retrieved = now
            data.content = content
            self.session.add(data)
        return self.session.merge(data)
    
    
