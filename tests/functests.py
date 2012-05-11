import time
import unittest
import requests

from urlparse import urljoin
from tcelery.utils import from_json


class TestCase(unittest.TestCase):
    base_url = "http://localhost:8888"

    def post(self, url, data=None):
        data = data or {}
        response = requests.post(urljoin(self.base_url, url), data=data)
        msg = from_json(response.content) if response.ok else None
        return response, msg

    def get(self, url, data=None):
        data = data or {}
        response = requests.get(urljoin(self.base_url, url), data=data)
        return response, from_json(response.content)


class AsyncTaskTests(TestCase):
    def test_acync_apply(self):
        response, msg = self.post('/async-apply/tasks.echo/',
                                  data={'args': 'foo'})
        self.assertTrue(response.ok)
        task_id =  msg['task-id']

        time.sleep(0.25)

        response, msg = self.get('/tasks/result/%s/' % task_id)
        self.assertTrue(response.ok)
        self.assertEqual('SUCCESS', msg['state'])
        self.assertEqual("foo", msg['result'])

    def test_async_apply_with_args(self):
        response, msg = self.post('/async-apply/tasks.add/',
                                  data={'args': [1, 2]})
        self.assertTrue(response.ok)
        task_id =  msg['task-id']

        time.sleep(0.25)

        response, msg = self.get('/tasks/result/%s/' % task_id)
        self.assertTrue(response.ok)
        self.assertEqual('SUCCESS', msg['state'])
        self.assertEqual(3, msg['result'])

    def test_unknown_task(self):
        response, msg = self.post('/async-apply/foo/')
        self.assertFalse(response.ok)
    
    @unittest.skip('no way to validate invalid task ids')
    def test_unknown_task_status(self):
        response, msg = self.get('/tasks/result/%s/' % 'foo')
        self.assertFalse(response.ok)


class TaskTests(TestCase):
    def test_apply(self):
        response, msg = self.post('/apply/tasks.echo/', data={'args': 'foo'})
        self.assertTrue(response.ok)
        self.assertEqual('foo', msg['result'])

    def test_apply_with_timeout(self):
        response, msg = self.post('/apply/tasks.sleep/',
                                  data={'args': '5', 'timeout': 0.5})
        self.assertTrue(response.ok)
        self.assertFalse('result' in msg)

    def test_apply_with_args(self):
        response, msg = self.post('/apply/tasks.add/', data={'args': [1, 2]})
        self.assertTrue(response.ok)
        self.assertEqual(3, msg['result'])

    def test_unknown_task(self):
        response, msg = self.post('/apply/foo')
        self.assertFalse(response.ok)


class TaskStatusTests(TestCase):
    def test_registered_tasks(self):
        response, msg = self.get('/tasks/registered/')
        self.assertTrue(response.ok)
        tasks = ['tasks.add', 'tasks.echo']
        self.assertTrue(all([t in msg.values()[0] for t in tasks]))

    def test_active_tasks(self):
        response, msg = self.get('/tasks/active/')
        self.assertTrue(response.ok)

    def test_scheduled_tesks(self):
        response, msg = self.get('/tasks/scheduled/')
        self.assertTrue(response.ok)


class TimingTests(TestCase):
    def test_eta(self):
        response, msg = self.post('/apply/tasks.echo/',
                                  data={'args': 'foo', 'timeout': 0.5,
                                        'countdown': 5})
        self.assertTrue(response.ok)
        self.assertFalse('result' in msg)

    def test_expires(self):
        response, msg= self.post('/apply/tasks.echo/',
                                 data={'args': 'foo',
                                       'countdown': 5, 'expires': 1})
        self.assertTrue(response.ok)
        self.assertEqual('REVOKED', msg['state'])
        self.assertFalse('result' in msg)


if __name__ == "__main__":
    unittest.main()
