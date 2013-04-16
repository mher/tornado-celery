from __future__ import absolute_import

import logging

from tornado import ioloop
from tornado import httpserver
from tornado.options import options, define, parse_command_line

from .app import Application
from . import setup_nonblocking_producer


define("port", default=8888, type=bool, help="run on the given port")


def main():
    parse_command_line()

    logging.info("Starting http server on port %s..." % options.port)
    http_server = httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    setup_nonblocking_producer()
    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
