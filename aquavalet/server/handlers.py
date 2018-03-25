import tornado.web



class StatusHandler(tornado.web.RequestHandler):

    def get(self):
        """List information about aquavalet status"""
        self.write({
            'status': 'up',
        })
