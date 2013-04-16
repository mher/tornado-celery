from __future__ import absolute_import

import celery

from tornado import ioloop

from .producer import AsyncTaskProducer, PikaClient


VERSION = (0, 2, 0)
__version__ = '.'.join(map(str, VERSION))


def setup_nonblocking_producer(celery_app=None, io_loop=None):
    celery_app = celery_app or celery.current_app
    io_loop = io_loop or ioloop.IOLoop.instance()

    AsyncTaskProducer.app = celery_app
    AsyncTaskProducer.producer = PikaClient()
    celery.app.amqp.AMQP.producer_cls = AsyncTaskProducer

    def connect():
        broker_url = celery_app.connection().as_uri(include_password=True)
        AsyncTaskProducer.producer.connect(broker_url)

    io_loop.add_callback(connect)
