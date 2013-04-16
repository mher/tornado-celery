from __future__ import absolute_import
from __future__ import with_statement

from datetime import timedelta
from functools import partial

from tornado import web
from tornado import ioloop
from tornado.escape import json_decode

from celery.result import AsyncResult
from celery.task.control import inspect
from celery.task.control import revoke
from celery.utils import uuid

from .utils import route


class ApplyHandlerBase(web.RequestHandler):

    def get_task_args(self):
        "extracts task args from a request"
        options = json_decode(self.request.body)
        args = options.pop('args', [])
        kwargs = options.pop('kwargs', {})
        return args, kwargs, options


@route('/async-apply/(.*)/')
class AsyncApplyHandler(ApplyHandlerBase):
    def post(self, taskname):
        try:
            task = self.application.celery_app.tasks[taskname]
        except KeyError:
            raise web.HTTPError(404, "Unknown task '%s'" % taskname)

        args, kwargs, options = self.get_task_args()
        result = task.apply_async(args=args, kwargs=kwargs, **options)
        self.write({'task-id': result.task_id, 'state': result.state})


@route('/tasks/result/(.*)/')
class TaskResultHandler(web.RequestHandler):
    def get(self, task_id):
        result = AsyncResult(task_id, app=self.application.celery_app)
        response = {'task-id': task_id, 'state': result.state}
        if result.ready():
            response.update({'result': result.result}) 
        self.write(response)


@route('/tasks/revoke/(.*)/')
class TaskRevokeHandler(web.RequestHandler):
    def delete(self, task_id):
        revoke(task_id)
        self.write({'task-id': task_id})


@route('/apply/(.*)/')
class ApplyHandler(ApplyHandlerBase):

    @web.asynchronous
    def post(self, taskname):
        try:
            task = self.application.celery_app.tasks[taskname]
        except KeyError:
            raise web.HTTPError(404, "Unknown task '%s'" % taskname)

        args, kwargs, options = self.get_task_args()
        timeout = options.pop('timeout', None)
        task_id = uuid()

        htimeout = None
        if timeout:
            htimeout = ioloop.IOLoop.instance().add_timeout(
                    timedelta(seconds=timeout),
                    partial(self.on_time, task_id))

        task.apply_async(args=args, kwargs=kwargs, task_id=task_id,
                         callback=partial(self.on_complete, htimeout),
                         **options)

    def on_complete(self, htimeout, result):
        if self._finished:
            return
        if htimeout:
            ioloop.IOLoop.instance().remove_timeout(htimeout)
        response = {'task-id': result.task_id, 'state': result.state}
        if result.successful():
            response.update({'result': result.result})
        self.write(response)
        self.finish()
    
    def on_time(self, task_id):
        revoke(task_id)
        result = AsyncResult(task_id, app=self.application.celery_app)
        self.write({'task-id': task_id, 'state': result.state})
        self.finish()


@route('/')
class MainHandler(web.RequestHandler):
    def get(self):
        self.write("Tasks: ")
        self.write(', '.join(filter(lambda x: not x.startswith('celery'),
                             self.application.celery_app.tasks.keys())))
