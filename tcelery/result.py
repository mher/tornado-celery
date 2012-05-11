from __future__ import absolute_import
from __future__ import with_statement

from functools import partial

from tornado import ioloop

from .handlers import ApplyHandler


class PeriodicResultChecker(object):
    def __init__(self, io_loop=None, interval=100):
        self.io_loop = io_loop or ioloop.IOLoop.instance()
        self.periodic_callback = ioloop.PeriodicCallback(
                partial(self.on_time, self), interval, self.io_loop)

    def task_complete(self, event):
        self.io_loop.add_callback(partial(ApplyHandler.on_complete, event))

    def on_time(self, *args):
        tasks = ApplyHandler.tasks
        completed = filter(lambda task_id:tasks[task_id][0].ready(), tasks)
        for task_id in completed:
            ApplyHandler.on_complete(task_id)

    def start(self):
        self.periodic_callback.start()

