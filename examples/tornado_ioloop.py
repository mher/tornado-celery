import tasks
import tcelery

from tornado import ioloop


def handle_result(result):
    print(result.result)
    ioloop.IOLoop.instance().stop()


def call_task():
    tasks.add.apply_async(args=[1, 2], callback=handle_result)


tcelery.setup_nonblocking_producer(on_ready=call_task)
ioloop.IOLoop.instance().start()
