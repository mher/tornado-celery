from __future__ import absolute_import

import sys
import time

from tornado import ioloop

from celery import Celery


celery1 = Celery('tasks', broker='amqp://')
celery2 = Celery('tasks', broker='amqp://')


@celery1.task
def add(x, y):
    return x + y


@celery2.task
def echo(x):
    return x


def bench_apply_async(ntimes):
    time_start = time.time()
    for i in range(ntimes):
        add.apply_async(args=[i, i])
    print("apply_async called {} times in {} seconds".format(
        ntimes, time.time() - time_start))


def bench_apply_async_nonblocking(ntimes, stop_io_loop=False):
    io_loop = ioloop.IOLoop.instance()

    def publish():
        time_start = time.time()
        for i in range(ntimes):
            echo.apply_async(args=[i])
        print("non blocking apply_async called {} times in {} seconds".format(
                ntimes, time.time() - time_start))
        if stop_io_loop:
            io_loop.stop()

    import tcelery
    tcelery.setup_nonblocking_producer(celery_app=celery2,
                                       io_loop=io_loop,
                                       on_ready=publish)
    io_loop.start()


if __name__ == "__main__":
    ntimes = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    method = sys.argv[2] if len(sys.argv) == 3 else None
    try:
        if method:
            vars()[method](ntimes)
        else:
            bench_apply_async(ntimes)
            bench_apply_async_nonblocking(ntimes)
    except KeyboardInterrupt:
        pass
