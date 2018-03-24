import tornado.web



class StatusHandler(tornado.web.RequestHandler):

    def get(self):
        """List information about waterbutler status"""
        self.write({
            'status': 'up',
        })
