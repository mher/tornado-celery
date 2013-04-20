from __future__ import absolute_import

import celery

from tornado import ioloop

from .producer import NonBlockingTaskProducer, Connection


VERSION = (0, 2, 0)
__version__ = '.'.join(map(str, VERSION))


def setup_nonblocking_producer(celery_app=None, io_loop=None, on_ready=None):
    celery_app = celery_app or celery.current_app
    io_loop = io_loop or ioloop.IOLoop.instance()

    NonBlockingTaskProducer.app = celery_app
    NonBlockingTaskProducer.connection = Connection()
    celery.app.amqp.AMQP.producer_cls = NonBlockingTaskProducer

    def connect():
        broker_url = celery_app.connection().as_uri(include_password=True)
        NonBlockingTaskProducer.producer.connect(broker_url, on_ready)

    io_loop.add_callback(connect)
