Usage
=====

Calling Celery tasks from Tornado RequestHandler: ::

    from tornado import gen, web
    import tcelery, tasks

    tcelery.setup_nonblocking_producer()

    class AsyncHandler(web.RequestHandler):
        @asynchronous
        def get(self):
            tasks.echo.apply_async(args=['Hello world!'], callback=self.on_result)

        def on_result(self, response):
            self.write(str(response.result))
            self.finish()

Calling tasks with generator-based interface: ::

    class GenAsyncHandler(web.RequestHandler):
        @asynchronous
        @gen.coroutine
        def get(self):
            response = yield gen.Task(tasks.sleep.apply_async, args=[3])
            self.write(str(response.result))
            self.finish()

**NOTE:** Currently callbacks only work with AMQP backend

