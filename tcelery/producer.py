from __future__ import absolute_import

import pickle
import timedelta

from functools import partial

from celery.app.amqp import TaskProducer
from celery.backends.amqp import AMQPBackend
from celery.utils import timeutils

from .result import AsyncResult


class NonBlockingTaskProducer(TaskProducer):

    conn_pool = None
    app = None

    def __init__(self, channel=None, *args, **kwargs):
        super(NonBlockingTaskProducer, self).__init__(
                channel, *args, **kwargs)

    def publish(self, body, routing_key=None, delivery_mode=None,
                mandatory=False, immediate=False, priority=0,
                content_type=None, content_encoding=None, serializer=None,
                headers=None, compression=None, exchange=None, retry=False,
                retry_policy=None, declare=[], **properties):
        headers = {} if headers is None else headers
        retry_policy = {} if retry_policy is None else retry_policy
        routing_key = self.routing_key if routing_key is None else routing_key
        compression = self.compression if compression is None else compression
        exchange = exchange or self.exchange

        callback = properties.pop('callback', None)
        task_id = body['id']

        if callback and not callable(callback):
            raise ValueError('callback should be callable')
        if callback and not isinstance(self.app.backend, AMQPBackend):
            raise NotImplementedError(
                    'callback can be used only with AMQP backend')

        body, content_type, content_encoding = self._prepare(
            body, serializer, content_type, content_encoding,
            compression, headers)

        conn = self.conn_pool.connection()
        publish = conn.publish
        result = publish(body, priority=priority, content_type=content_type,
                         content_encoding=content_encoding, headers=headers,
                         properties=properties, routing_key=routing_key,
                         mandatory=mandatory, immediate=immediate,
                         exchange=exchange, declare=declare)

        if callback:
            conn.consume(task_id.replace('-', ''),
                         partial(self.on_result, callback),
                         x_expires=self.prepare_expires(type=int))
        return result

    def on_result(self, callback, method, channel, deliver, reply):
        reply = pickle.loads(reply)
        callback(AsyncResult(**reply))

    def prepare_expires(self, value=None, type=None):
        if value is None:
            value = self.app.conf.CELERY_TASK_RESULT_EXPIRES
        if isinstance(value, timedelta):
            value = timeutils.timedelta_seconds(value)
        if value is not None and type:
            return type(value)
        return value

    def __repr__(self):
        return '<NonBlockingTaskProducer: {0.channel}>'.format(self)
