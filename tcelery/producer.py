from __future__ import absolute_import

import pickle

from urlparse import urlparse
from functools import partial

import pika

from celery.app.amqp import TaskProducer
from celery.backends.amqp import AMQPBackend
from pika.adapters.tornado_connection import TornadoConnection

from .result import AsyncResult


class PikaClient(object):

    content_type = 'application/x-python-serialize'

    def __init__(self):
        self.channel = None
        self.connection = None

    def connect(self, url, callback=None):
        purl = urlparse(url)
        credentials = pika.PlainCredentials(purl.username, purl.password)
        virtual_host = purl.path[1:]
        host = purl.hostname
        port = purl.port

        params = pika.ConnectionParameters(host, port, virtual_host, credentials)
        self.connection = TornadoConnection(
                params, on_open_callback=partial(self.on_connect, callback))
        self.connection.add_on_close_callback(self.on_closed)

    def on_connect(self, callback, connection):
        self.connection = connection
        connection.channel(partial(self.on_channel_open, callback))

    def on_channel_open(self, callback, channel):
        self.channel = channel
        if callback:
            callback()

    def on_exchange_declare(self, frame):
        pass

    def on_basic_cancel(self, frame):
        self.connection.close()

    def on_closed(self, connection):
        pass

    def publish(self, body, exchange=None, routing_key=None,
                mandatory=False, immediate=False, content_type=None,
                content_encoding=None, serializer=None,
                headers=None, compression=None, retry=False,
                retry_policy=None, declare=[], **properties):
        assert self.channel
        content_type = content_type or self.content_type

        properties = pika.BasicProperties(
                content_type=content_type,
                )

        self.channel.basic_publish(
                exchange=exchange, routing_key=routing_key, body=body,
                properties=properties, mandatory=mandatory,
                immediate=immediate)

    def consume(self, queue, callback, x_expires=None):
        assert self.channel
        self.channel.queue_declare(self.on_queue_declared, queue=queue,
                exclusive=False, auto_delete=True, nowait=True,
                arguments={'x-expires': x_expires})
        self.channel.basic_consume(callback, queue, no_ack=True)

    def on_queue_declared(self, *args, **kwargs):
        pass


class AsyncTaskProducer(TaskProducer):

    producer = None
    app = None

    def __init__(self, *args, **kwargs):
        super(AsyncTaskProducer, self).__init__(*args, **kwargs)

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
            raise NotImplementedError('callback can be used only with AMQP backend')

        body, content_type, content_encoding = self._prepare(
            body, serializer, content_type, content_encoding,
            compression, headers)

        publish = self.producer.publish
        result = publish(body, priority=priority, content_type=content_type,
                       content_encoding=content_encoding, headers=headers,
                       properties=properties, routing_key=routing_key,
                       mandatory=mandatory, immediate=immediate,
                       exchange=exchange, declare=declare)

        if callback:
            x_expires = int(self.app.conf.CELERY_TASK_RESULT_EXPIRES.total_seconds()*1000)
            self.producer.consume(task_id.replace('-', ''),
                                  partial(self.on_result, callback),
                                  x_expires=x_expires)

        return result

    def on_result(self, callback, method, channel, deliver, reply):
        reply = pickle.loads(reply)
        callback(AsyncResult(**reply))
