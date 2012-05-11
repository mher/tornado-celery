from urllib import urlencode

from tornado import ioloop
from tornado import httpclient


def handle_request(response):
    if response.error:
        print "Error:", response.error
    else:
        print response.body
    ioloop.IOLoop.instance().stop()


http_client = httpclient.AsyncHTTPClient()
http_client.fetch("http://localhost:8888/apply/tasks.sleep",
                  handle_request, method="POST",
                  body=urlencode({"args": 3}))
ioloop.IOLoop.instance().start()
