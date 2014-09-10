from functools import wraps
from examples import redis_tasks
from tcelery import setup_nonblocking_producer
from tornado.testing import AsyncTestCase
from tornado.ioloop import IOLoop


def with_nonblocking_producer(app):
    def wrapped(f):
        @wraps(f)
        def inner(self):
            setup_nonblocking_producer(app, self.io_loop,
                                       on_ready=lambda: f(self))
            self.wait()
        return inner
    return wrapped


class RedisTests(AsyncTestCase):
    def get_new_ioloop(self):
        return IOLoop.instance()

    @with_nonblocking_producer(redis_tasks.celery)
    def test_async(self):
        def done(response):
            self.assertEqual("hello", response.result)
            # redis_tasks.celery.close()
            self.stop()
        redis_tasks.echo.apply_async(args=['hello'], callback=done)

    @with_nonblocking_producer(redis_tasks.celery)
    def test_async_with_mult_args(self):
        def done(response):
            self.assertEqual(3, response.result)
            self.stop()
        redis_tasks.add.apply_async(args=[1, 2], callback=done)

    @with_nonblocking_producer(redis_tasks.celery)
    def test_async_with_kwargs(self):
        def done(response):
            self.assertTrue(response.result.endswith("hello"))
            self.stop()
        redis_tasks.echo.apply_async(
            args=['hello'], kwargs={'timestamp': True}, callback=done)
