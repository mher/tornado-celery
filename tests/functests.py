import time
import unittest
import requests

from urlparse import urljoin
from tornado import ioloop, gen
from tornado.escape import json_encode, json_decode

from examples import tasks


class TestCase(unittest.TestCase):
    base_url = "http://localhost:8888"

    def post(self, url, data=None):
        data = json_encode(data or {})
        response = requests.post(urljoin(self.base_url, url), data=data)
        msg = json_decode(response.content) if response.ok else None
        return response, msg

    def get(self, url, data=None):
        data = json_encode(data or {})
        response = requests.get(urljoin(self.base_url, url), data=data)
        return response, json_decode(response.content)


class AsyncTaskTests(TestCase):
    def test_acync_apply(self):
        response, msg = self.post('/apply-async/tasks.echo/',
                                  data={'args': ['foo']})
        self.assertTrue(response.ok)
        task_id = msg['task-id']

        time.sleep(0.25)

        response, msg = self.get('/tasks/result/%s/' % task_id)
        self.assertTrue(response.ok)
        self.assertEqual('SUCCESS', msg['state'])
        self.assertEqual("foo", msg['result'])

    def test_apply_async_with_args(self):
        response, msg = self.post('/apply-async/tasks.add/',
                                  data={'args': [1, 2]})
        self.assertTrue(response.ok)
        task_id = msg['task-id']

        time.sleep(0.25)

        response, msg = self.get('/tasks/result/%s/' % task_id)
        self.assertTrue(response.ok)
        self.assertEqual('SUCCESS', msg['state'])
        self.assertEqual(3, msg['result'])

    def test_apply_async_with_kwargs(self):
        response, msg = self.post('/apply-async/tasks.echo/',
                                  data={'args': ['foo'],
                                        'kwargs': {'timestamp': True}})
        self.assertTrue(response.ok)
        task_id = msg['task-id']

        time.sleep(0.25)

        response, msg = self.get('/tasks/result/%s/' % task_id)
        self.assertTrue(response.ok)
        self.assertEqual('SUCCESS', msg['state'])
        self.assertTrue(msg['result'].endswith('foo'))

    def test_unknown_task(self):
        response, msg = self.post('/apply-async/foo/')
        self.assertFalse(response.ok)

    @unittest.skip('no way to validate invalid task ids')
    def test_unknown_task_status(self):
        response, msg = self.get('/tasks/result/%s/' % 'foo')
        self.assertFalse(response.ok)


class TaskTests(TestCase):
    def test_apply(self):
        response, msg = self.post('/apply/tasks.echo/', data={'args': ['foo']})
        self.assertTrue(response.ok)
        self.assertEqual('foo', msg['result'])

    def test_apply_with_timeout(self):
        response, msg = self.post('/apply/tasks.sleep/',
                                  data={'args': [5], 'timeout': 0.5})
        self.assertTrue(response.ok)
        self.assertFalse('result' in msg)

    def test_apply_with_args(self):
        response, msg = self.post('/apply/tasks.add/', data={'args': [1, 2]})
        self.assertTrue(response.ok)
        self.assertEqual(3, msg['result'])

    def test_unknown_task(self):
        response, msg = self.post('/apply/foo')
        self.assertFalse(response.ok)


class TimingTests(TestCase):
    def test_eta(self):
        response, msg = self.post('/apply/tasks.echo/',
                                  data={'args': ['foo'], 'timeout': 0.5,
                                        'countdown': 5})
        self.assertTrue(response.ok)
        self.assertFalse('result' in msg)

    def test_expires(self):
        response, msg = self.post('/apply/tasks.echo/',
                                  data={'args': ['foo'],
                                        'countdown': 5, 'expires': 1})
        self.assertTrue(response.ok)
        self.assertEqual('REVOKED', msg['state'])
        self.assertFalse('result' in msg)


class TaskClassTests(unittest.TestCase):
    def test_async(self):
        def done(response):
            ioloop.IOLoop.instance().stop()
            self.assertEqual("hello", json_decode(response.body)["result"])
        yield gen.Task(tasks.echo.apply_async, args=['hello'], callback=done)
        ioloop.IOLoop.instance().start()

    def test_async_with_mult_args(self):
        def done(response):
            ioloop.IOLoop.instance().stop()
            self.assertEqual(3, json_decode(response.body)["result"])
        yield gen.Task(tasks.add.apply_async, args=[1, 2], callback=done)
        ioloop.IOLoop.instance().start()

    def test_async_with_kwargs(self):
        def done(response):
            ioloop.IOLoop.instance().stop()
            result = json_decode(response.body)["result"]
            self.assertTrue(result.endswith("hello"))
        yield gen.Task(tasks.echo, args=['hello'], kwargs={'timestamp': True},
                       callback=done)
        ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    unittest.main()
