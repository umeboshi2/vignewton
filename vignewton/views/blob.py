from datetime import datetime

from pyramid.response import Response

from vignewton.models.sitecontent import SiteImage


class BlobViewer(object):
    def __init__(self, request):
        self.request = request
        self.content = {}
        self.filetype = None
        if 'filetype' in self.request.matchdict:
            self.filetype = self.request.matchdict['filetype']

        self.db = self.request.db

        # make dispatch table
        self._viewmap = dict(
            image=self.get_image,
            thumb=self.get_thumb,)

        # dispatch filetype request
        if self.filetype in self._viewmap:
            self._viewmap[self.filetype]()
        else:
            self.content = HTTPNotFound()
            
    def __call__(self):
        return self.content

    def get_image(self):
        id = self.request.matchdict['id']
        i = self.db.query(SiteImage).get(id)

        content = i.content
        # FIXME
        content_type = 'image/png'
        response = Response(body=i.content,
                            content_type=content_type)
        self.content = response
    
    def get_thumb(self):
        id = self.request.matchdict['id']
        i = self.db.query(SiteImage).get(id)
        # FIXME
        content_type = 'image/jpeg'
        response = Response(body=i.thumbnail,
                            content_type=content_type)
        self.content = response
    
