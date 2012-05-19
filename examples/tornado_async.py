from tornado import gen
from tornado import ioloop
from tornado.web import asynchronous, RequestHandler, Application

from tcelery import Task


class AsyncHandler(RequestHandler):
    @asynchronous
    def get(self):
        Task("tasks.sleep", callback=self.on_task_complete)(3)

    def on_task_complete(self, response):
        self.write("Completed!")
        self.finish()


class GenAsyncHandler(RequestHandler):
    @asynchronous
    @gen.engine
    def get(self):
        response = yield Task("tasks.sleep", 3)
        self.write(str(response.body))
        self.finish()


class GenMultipleAsyncHandler(RequestHandler):
    @asynchronous
    @gen.engine
    def get(self):
        r1, r2 = yield [Task("tasks.sleep", 3), Task("tasks.add", 1, 2)]
        self.write(str(r1.body))
        self.write(str(r2.body))
        self.finish()


application = Application([
    (r"/async-sleep", AsyncHandler),
    (r"/gen-async-sleep", GenAsyncHandler),
    (r"/gen-async-sleep-add", GenMultipleAsyncHandler),
])


if __name__ == "__main__":
    application.listen(8887)
    ioloop.IOLoop.instance().start()
