import tornado.ioloop
import tornado.web
import logging
from smsvc import smsvc


class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, mobile):
        vc = smsvcsender.sendsmsvc(mobile)
        self.write('{"mobile":"%s","vc":"%s"}' % (mobile, vc))
        self.finish()

application = tornado.web.Application([
    (r"/sendvc/([0-9]+)", MainHandler),
])

if __name__ == "__main__":
    logging.basicConfig(filename='smsvcserver.log', level=logging.INFO)
    smsvcsender = smsvc()
    smsvcsender.start()
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
