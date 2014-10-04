from __future__ import absolute_import

import celery

from tornado import web
from tornado.options import define, options

from . import handlers as _  # noqa
from .utils import route


define("debug", type=bool, default=False, help="run in debug mode")


class Application(web.Application):
    def __init__(self, celery_app=None):
        handlers = route.get_routes()
        settings = dict(debug=options.debug)
        super(Application, self).__init__(handlers, **settings)
        self.celery_app = celery_app or celery.Celery()
