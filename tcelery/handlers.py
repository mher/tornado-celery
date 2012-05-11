from __future__ import absolute_import
from __future__ import with_statement

from datetime import timedelta
from functools import partial

from tornado import web
from tornado import ioloop
from tornado.options import options as tornado_options

from celery.result import AsyncResult
from celery.task.control import inspect
from celery.task.control import revoke
from celery.execute import send_task

from .utils import route, to_json


class ApplyHandlerBase(web.RequestHandler):
    registered_tasks = []

    def get_task_args(self):
        options = dict(self.request.arguments)
        args = options.pop('args', [])
        kwargs = options.pop('kwargs', {})
        for o, v in options.iteritems():
            options[o] = v[0]
            try:
                options[o] = float(v[0])
                options[o] = int(v[0])
            except:
                pass
        return args, kwargs, options

    @classmethod
    def get_registered_tasks(cls):
        if not cls.registered_tasks:
            i = inspect()
            tasks = []
            for rt in i.registered().itervalues():
                tasks.extend(rt)
            cls.registered_tasks = set(tasks)

        return cls.registered_tasks


@route('/async-apply/(.*)/')
class AsyncApplyHandler(ApplyHandlerBase):
    def post(self, taskname):
        if taskname not in self.get_registered_tasks():
            raise web.HTTPError(404)

        args, kwargs, options = self.get_task_args()
        result = send_task(taskname, args=args, kwargs=kwargs)
        self.write(to_json({'task-id': result.task_id, 'state': result.state}))


@route('/tasks/result/(.*)/')
class TaskResultHandler(web.RequestHandler):
    def get(self, task_id):
        result = AsyncResult(task_id)
        response = {'task-id': task_id, 'state': result.state}
        if result.ready():
            response.update({'result': result.result}) 
        self.write(to_json(response))


@route('/tasks/revoke/(.*)/')
class TaskRevokeHandler(web.RequestHandler):
    def delete(self, task_id):
        revoke(task_id)
        self.write(to_json({'task-id': task_id}))


@route('/apply/(.*)/')
class ApplyHandler(ApplyHandlerBase):
    tasks = {}

    @web.asynchronous
    def post(self, taskname):
        if not tornado_options.blocking:
            raise web.HTTPError(503)
        if taskname not in self.get_registered_tasks():
            raise web.HTTPError(404)

        args, kwargs, options = self.get_task_args()
        timeout = options.pop('timeout', None)
        result = send_task(taskname, args=args, kwargs=kwargs, **options)

        htimeout = None
        if timeout:
            htimeout = ioloop.IOLoop.instance().add_timeout(
                    timedelta(seconds=timeout),
                    partial(ApplyHandler.on_time, result.task_id))

        self.tasks[result.task_id] = (result, self, htimeout)

    @classmethod
    def on_complete(cls, task_id):
        result, handler, htimeout = cls.tasks.pop(task_id)
        response = {'task-id': task_id, 'state': result.state}
        if result.successful():
            response.update({'result': result.result})
        handler.write(to_json(response))
        if htimeout:
            ioloop.IOLoop.instance().remove_timeout(htimeout)
        handler.finish()
    
    @classmethod
    def on_time(cls, task_id):
        result, handler, _ = cls.tasks.pop(task_id)
        revoke(task_id)
        handler.write(to_json({'task-id': task_id, 'state': result.state}))
        handler.finish()


@route('/tasks/registered/(.*)')
class RegisteredTaskHandler(web.RequestHandler):
    def get(self, host):
        host = [host] if host else None
        i = inspect(host)
        self.write(to_json(i.registered()))


@route('/tasks/active/(.*)')
class ActiveTaskHandler(web.RequestHandler):
    def get(self, host):
        host = [host] if host else None
        i = inspect(host)
        self.write(to_json(i.active()))


@route('/tasks/scheduled/(.*)')
class ScheduledTaskHandler(web.RequestHandler):
    def get(self, host):
        host = [host] if host else None
        i = inspect(host)
        self.write(to_json(i.active()))


@route('/')
class MainHandler(web.RequestHandler):
    def get(self):
        self.write("Tasks: ")
        self.write(unicode(ApplyHandler.tasks))
