from __future__ import absolute_import

import logging

from tornado import ioloop
from tornado import httpserver
from tornado.options import options, define, parse_command_line

from .app import Application
from .result import PeriodicResultChecker


define("port", default=8888, type=bool, help="run on the given port")
define("blocking", default=False, type=bool, help="enable blocking mode")


def main():
    parse_command_line()

    if options.blocking:
        result_checker = PeriodicResultChecker()
        result_checker.start()

    logging.info("Starting http server on port %s..." % options.port)
    http_server = httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
