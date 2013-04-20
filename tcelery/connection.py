from __future__ import absolute_import

from urlparse import urlparse
from functools import partial

import pika

from pika.adapters.tornado_connection import TornadoConnection


class Connection(object):

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

        params = pika.ConnectionParameters(host, port, virtual_host,
                                           credentials)
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

        properties = pika.BasicProperties(content_type=content_type)

        self.channel.basic_publish(
                exchange=exchange, routing_key=routing_key, body=body,
                properties=properties, mandatory=mandatory,
                immediate=immediate)

    def consume(self, queue, callback, x_expires=None):
        assert self.channel
        self.channel.queue_declare(self.on_queue_declared, queue=queue,
                                   exclusive=False, auto_delete=True,
                                   nowait=True,
                                   arguments={'x-expires': x_expires})
        self.channel.basic_consume(callback, queue, no_ack=True)

    def on_queue_declared(self, *args, **kwargs):
        pass
