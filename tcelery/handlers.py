from __future__ import absolute_import
from __future__ import with_statement

from datetime import timedelta
from functools import partial

from tornado import web
from tornado import ioloop
from tornado.escape import json_decode

from celery.result import AsyncResult
from celery.task.control import revoke
from celery.utils import uuid

from .utils import route


class ApplyHandlerBase(web.RequestHandler):
    def get_task_args(self):
        "extracts task args from a request"
        try:
            options = json_decode(self.request.body)
        except (TypeError, ValueError):
            raise web.HTTPError(400)
        args = options.pop('args', [])
        kwargs = options.pop('kwargs', {})
        if not isinstance(args, (list, tuple)):
            raise web.HTTPError(400, 'task args must be a list or tuple')

        return args, kwargs, options


@route('/apply-async/(.*)/')
class ApplyAsyncHandler(ApplyHandlerBase):
    def post(self, taskname):
        """
Apply tasks asynchronously by sending a message

**Example request**:

.. sourcecode:: http

    POST /apply-async/examples.tasks.add/ HTTP/1.1
    Accept: application/json
    Accept-Encoding: gzip, deflate, compress
    Content-Length: 16
    Content-Type: application/json; charset=utf-8
    Host: localhost:8888
    User-Agent: HTTPie/0.8.0

    {
        "args": [
            1,
            2
        ]
    }


**Example response**:

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Length: 71
    Content-Type: application/json; charset=UTF-8
    Server: TornadoServer/3.2

    {
        "state": "PENDING",
        "task-id": "1c9be31f-3094-4319-8895-ad2f0654c699"
    }

:statuscode 200: no error
:statuscode 400: invalid request
:statuscode 404: unknown task
        """
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
        """
Get task result by task-id

**Example request**:

.. sourcecode:: http

    GET /tasks/result/9ec42ba0-be59-488f-a445-4a007d83b954/ HTTP/1.1
    Accept: application/json
    Accept-Encoding: gzip, deflate, compress
    Content-Type: application/json; charset=utf-8
    Host: localhost:8888
    User-Agent: HTTPie/0.8.0

**Example response**:

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Length: 84
    Content-Type: application/json; charset=UTF-8
    Etag: "0aef8448588cf040f1daa7a0244c0a7b93abfd71"
    Server: TornadoServer/3.2

    {
        "result": 3,
        "state": "SUCCESS",
        "task-id": "9ec42ba0-be59-488f-a445-4a007d83b954"
    }

:statuscode 200: no error
:statuscode 400: invalid request
        """
        result = AsyncResult(task_id, app=self.application.celery_app)
        response = {'task-id': task_id, 'state': result.state}
        if result.ready():
            if result.successful():
                response['result'] = result.result
            else:
                response['traceback'] = result.traceback
                response['error'] = result.result
        self.write(response)


@route('/tasks/revoke/(.*)/')
class TaskRevokeHandler(web.RequestHandler):
    def delete(self, task_id):
        """
Revoke a task

**Example request**:

.. sourcecode:: http

    DELETE /tasks/revoke/d776e835-33ac-447f-b27d-bb8529718ae6/ HTTP/1.1
    Accept: application/json
    Accept-Encoding: gzip, deflate, compress
    Content-Length: 0
    Content-Type: application/json; charset=utf-8
    Host: localhost:8888
    User-Agent: HTTPie/0.8.0

**Example response**:

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Length: 51
    Content-Type: application/json; charset=UTF-8
    Server: TornadoServer/3.2

    {
        "task-id": "d776e835-33ac-447f-b27d-bb8529718ae6"
    }

:statuscode 200: no error
:statuscode 400: invalid request
        """
        revoke(task_id)
        self.write({'task-id': task_id})


@route('/apply/(.*)/')
class ApplyHandler(ApplyHandlerBase):
    @web.asynchronous
    def post(self, taskname):
        """
Apply tasks synchronously. Function returns when the task is finished

**Example request**:

.. sourcecode:: http

    POST /apply/examples.tasks.add/ HTTP/1.1
    Accept: application/json
    Accept-Encoding: gzip, deflate, compress
    Content-Length: 16
    Content-Type: application/json; charset=utf-8
    Host: localhost:8888
    User-Agent: HTTPie/0.8.0

    {
        "args": [
            1,
            2
        ]
    }

**Example response**:

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Length: 84
    Content-Type: application/json; charset=UTF-8
    Server: TornadoServer/3.2

    {
        "result": 3,
        "state": "SUCCESS",
        "task-id": "2ce70595-a028-4e0d-b906-be2183fc6821"
    }

:statuscode 200: no error
:statuscode 400: invalid request
:statuscode 404: unknown task
        """
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
            response['result'] = result.result
        else:
            response['traceback'] = result.traceback
            response['error'] = repr(result.result)
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
