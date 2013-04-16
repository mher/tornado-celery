import time
import tasks

from functools import partial
from tornado import ioloop

import tcelery
tcelery.setup_nonblocking_producer()


def handle_result(result):
    print(result.result)
    ioloop.IOLoop.instance().stop()


io_loop = ioloop.IOLoop.instance()
io_loop.add_timeout(time.time() + 1,
                    partial(tasks.add.apply_async, args=[1, 2],
                            callback=handle_result))
io_loop.start()
