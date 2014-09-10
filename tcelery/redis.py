from functools import partial

from tornado import gen
from tornadoredis import Client
from tornadoredis.exceptions import ResponseError
from tornadoredis.pubsub import BaseSubscriber


class CelerySubscriber(BaseSubscriber):
    def unsubscribe_channel(self, channel_name):
        """Unsubscribes the redis client from the channel"""
        del self.subscribers[channel_name]
        del self.subscriber_count[channel_name]
        self.redis.unsubscribe(channel_name)

    def on_message(self, msg):
        if not msg:
            return
        if msg.kind == 'message' and msg.body:
            # Get the list of subscribers for this channel
            for subscriber in self.subscribers[msg.channel].keys():
                subscriber(msg.body)
        super(CelerySubscriber, self).on_message(msg)


class RedisClient(Client):
    @gen.engine
    def _consume_bulk(self, tail, callback=None):
        response = yield gen.Task(self.connection.read, int(tail) + 2)
        if isinstance(response, Exception):
            raise response
        if not response:
            raise ResponseError('EmptyResponse')
        else:
            # We don't cast try to convert to unicode here as the response
            # may not be utf-8 encoded, for example if using msgpack as a
            # serializer
            # response = to_unicode(response)
            response = response[:-2]
        callback(response)


class RedisConsumer(object):
    def __init__(self, producer):
        self.producer = producer
        backend = producer.app.backend
        self.client = RedisClient(host=backend.host,
                                  port=backend.port,
                                  password=backend.password,
                                  selected_db=backend.db,
                                  io_loop=producer.conn_pool.io_loop)
        self.client.connect()
        self.subscriber = CelerySubscriber(self.client)

    def wait_for(self, task_id, callback, expires=None):
        # TODO: here we should add a timeout on ioloop to remove the callback
        # and unsubscribe the channel when the expires timeout is reached
        key = self.producer.app.backend.get_key_for_task(task_id)
        self.subscriber.subscribe(
            key, partial(self.on_result, key, callback))

    def on_result(self, key, callback, result):
        self.subscriber.unsubscribe_channel(key)
        callback(result)
