import tornado.web
from aquavalet.tasks.app import app
from aquavalet import settings

from aquavalet.providers.filesystem import FileSystemProvider

class StatusHandler(tornado.web.RequestHandler):

    def get(self):
        """List information about aquavalet status"""
        self.write({
            'status': 'up',
        })


class RootHandler(tornado.web.RequestHandler):

    def get(self):
        """List information about aquavalet status"""
        self.write({
            'patterns': {'root': settings.ROOT_PATTERN},
            'providers': [{'name': 'filesystem'},
                          {'name': 'waterbutler',
                           'pattern': ''},
                          ],
        })
