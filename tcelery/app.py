from __future__ import absolute_import

from tornado import web
from tornado.options import define, options

from . import handlers as _
from .utils import route


define("debug", type=bool, default=False, help="run in debug mode")


class Application(web.Application):
    def __init__(self):
        handlers = route.get_routes()
        settings = dict(debug=options.debug)
        super(Application, self).__init__(handlers, **settings)
