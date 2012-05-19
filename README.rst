tornado-celery: Celery integration with Tornado
===============================================

tornado-celery is an experimental tool intended to simplify the usage
of Celery in Tornado web framework. From one side tornado-celery is a
web application which exposes the functionality of Celery via the REST
interface (task are executed and controlled by HTTP **GET**, **POST**
and **DELETE** methods). From the other side it helps to call tasks and
asynchronously get the result from the RequestHandler.

Usage
-----

Launch the server: ::

    $ celeryr --blocking

And call tasks from Tornado RequestHandler: ::

    from tornado import gen, web
    from tcelery import Task

    class AsyncHandler(web.RequestHandler):
        @web.asynchronous
        def get(self):
            Task("tasks.sleep", callback=self.on_task_complete)(3)

        def on_task_complete(self, response):
            self.write("Done!")
            self.finish()

Or by using generator-based interface: ::

    class GenMultipleAsyncHandler(web.RequestHandler):
        @web.asynchronous
        @gen.engine
        def get(self):
            r1, r2 = yield [Task("tasks.sleep", 3), Task("tasks.add", 1, 2)]
            self.write(str(r1.body))
            self.write(str(r2.body))
            self.finish()

tornado-celery can be used to call Celery tasks from other languages and
environments.

Execute a task asynchronously: ::

    $ curl -X POST -d '{"args":["hello"]}' http://localhost:8888/async-apply/tasks.echo/
    {"task-id": "a24c9e38-4976-426a-83d6-6b10b4de7ab1", "state": "PENDING"}

Get the result: ::

    $ curl http://localhost:8888/tasks/result/a24c9e38-4976-426a-83d6-6b10b4de7ab1/
    {"task-id": "a24c9e38-4976-426a-83d6-6b10b4de7ab1", "state": "SUCCESS", "result": "hello"}

Execute a task and get the result: ::

    $ curl -X POST -d '{"args":[1,2]}' http://localhost:8888/apply/tasks.add/
    {"task-id": "fe3cc5a5-d11b-4b17-a6e2-e7fd2fba7ec6", "state": "SUCCESS", "result": 3}

Execute a task with timeout: ::

    $ curl -X POST -d '{"args":[5],"timeout":1}' http://localhost:8888/apply/tasks.sleep/
    {"task-id": "9ca78e26-bbb2-404c-b3bb-bc1c63cbdf41", "state": "REVOKED"}

List all registered tasks: ::

    $ curl http://localhost:8888/tasks/registered/
    {"localhost": ["celery.backend_cleanup", "celery.chain", "celery.chord", "celery.chord_unlock", "celery.chunks", "celery.group", "celery.map", "celery.starmap", "tasks.add", "tasks.echo", "tasks.error", "tasks.sleep"]}

List active tasks: ::

    $ curl http://localhost:8888/tasks/active/
    {"localhost": [{"hostname": "localhost", "time_start": 1337432111.714233, "name": "tasks.sleep", "delivery_info": {"routing_key": "celery", "exchange": "celery"}, "args": "[20]", "acknowledged": true, "kwargs": "{}", "id": "52385dc9-ed99-4e9a-9ce0-ff94a54cf565", "worker_pid": 5896}]}

List scheduled tasks: ::

    $ curl http://localhost:8888/tasks/scheduled/
    {"localhost": []}

Installation
------------

To install tornado-celery, simply: ::

    $ pip install git+git://github.com/mher/tornado-celery.git

