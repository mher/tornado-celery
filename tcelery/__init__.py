from __future__ import absolute_import

import celery

from tornado import ioloop

from .connection import ConnectionPool
from .producer import NonBlockingTaskProducer
from .result import AsyncResult

VERSION = (0, 3, 5)
__version__ = '.'.join(map(str, VERSION)) + '-dev'


def setup_nonblocking_producer(celery_app=None, io_loop=None,
                               on_ready=None, result_cls=AsyncResult,
                               limit=1, producer_cls=NonBlockingTaskProducer,
                               callback=None):
    """Setup celery to use non blocking producer

    :param celery_app:
    :param io_loop:
    :param on_ready: alias for callback
    :param result_cls:
    :param limit:
    :param producer_cls:
    :param callback: Callback after connection is established
    :return:

    :type limit: int
    :type io_loop: tornado.ioloop.IOLoop
    :type on_ready: Function
    :type callback: Function
    """

    if on_ready is not None:
        assert callback is None, 'you may only supply either: on_ready or callback'
        callback = on_ready

    celery_app = celery_app or celery.current_app
    io_loop = io_loop or ioloop.IOLoop.instance()

    producer_cls.app = celery_app
    producer_cls.conn_pool = ConnectionPool(limit, io_loop)
    producer_cls.result_cls = result_cls
    if celery_app.conf['BROKER_URL'] and celery_app.conf['BROKER_URL'].startswith('amqp'):
        celery.app.amqp.AMQP.producer_cls = producer_cls

    def connect():
        broker_url = celery_app.connection().as_uri(include_password=True)
        options = celery_app.conf.get('CELERYT_PIKA_OPTIONS', {})
        producer_cls.conn_pool.connect(broker_url,
                                       options=options,
                                       callback=callback)

    io_loop.add_callback(connect)
