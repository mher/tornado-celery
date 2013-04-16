from __future__ import absolute_import

import logging

from pprint import pformat

from celery.bin.base import Command

from tornado import ioloop
from tornado import httpserver
from tornado.options import options, define, parse_command_line

from .app import Application
from . import setup_nonblocking_producer


define("port", default=8888, type=bool, help="run on the given port")


class TCeleryCommand(Command):

    def run_from_argv(self, prog_name, argv=None):
        argv = filter(self.tornado_option, argv)
        parse_command_line([prog_name] + argv)

        logging.info("Starting http server on port %s..." % options.port)
        http_server = httpserver.HTTPServer(Application(celery_app=self.app))
        http_server.listen(options.port)
        logging.info("Registered tasks:")
        logging.info(pformat(self.app.tasks.keys()))

        logging.info("Setting up non-blocking producer...")
        setup_nonblocking_producer()

        ioloop.IOLoop.instance().start()

    def handle_argv(self, prog_name, argv=None):
        return self.run_from_argv(prog_name, argv)

    @staticmethod
    def tornado_option(arg):
        name, _, value = arg.lstrip('-').partition("=")
        name = name.replace('-', '_')
        return hasattr(options, name)


def main():
    try:
        cmd = TCeleryCommand()
        cmd.execute_from_commandline()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
