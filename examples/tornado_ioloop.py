from tornado import ioloop

from tcelery import Task


def handle_request(response):
    if response.error:
        print "Error:", response.error
    else:
        print response.body
    ioloop.IOLoop.instance().stop()


Task("tasks.sleep", callback=handle_request)(3)
ioloop.IOLoop.instance().start()
