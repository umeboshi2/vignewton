import os
from datetime import datetime, timedelta
from zipfile import ZipFile, ZIP_DEFLATED
from cStringIO import StringIO
import cPickle as Pickle
from io import BytesIO
import csv

import transaction
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import or_



class InsufficientFundsError(Exception):
    pass

class AmountTooHighError(Exception):
    pass

class NoBetsManagerError(Exception):
    pass



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
            latest = self.get_latest_content()
            if latest is not None and latest.content == content:
                latest.retrieved = now
                latest = self.session.merge(latest)
            else:
                latest = self.dbmodel()
                latest.retrieved = now
                latest.content = content
                self.session.add(latest)
        return self.session.merge(latest)

    def _create_archive_files(self):
        fields = ['id', 'retrieved']
        self.zipfileobj = BytesIO()
        self.csvfileobj = StringIO()
        self.zipfile = ZipFile(self.zipfileobj, 'w', ZIP_DEFLATED)
        self.csvfile = csv.DictWriter(self.csvfileobj, fields)

    def _serialize_object(self, obj):
        fields = ['id', 'retrieved']
        return dict(id=obj.id, retrieved=obj.retrieved)
    
    
    def archive_table(self, objtype):
        self._create_archive_files()
        for obj in self.query().all():
            odict = self._serialize_object(obj)
            self.csvfile.writerow(odict)
            filename = '%s-%04d.pickle' % (objtype, obj.id)
            content = Pickle.dumps(obj.content)
            self.zipfile.writestr(filename, content)
        csvfilename = '%s-objects.csv' % objtype
        self.zipfile.writestr(csvfilename, self.csvfileobj.getvalue())
        self.zipfile.close()
        return self.zipfileobj.getvalue()
    
        
        
    
    
