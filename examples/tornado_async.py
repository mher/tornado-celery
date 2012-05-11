from urllib import urlencode

from tornado import gen
from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado.web import asynchronous, RequestHandler, Application


class AsyncHandler(RequestHandler):
    @asynchronous
    def get(self):
        http_client = AsyncHTTPClient()
        http_client.fetch("http://localhost:8888/apply/tasks.sleep",
                          callback=self.on_task_complete,
                          method="POST",
                          body=urlencode({"args": 3}))

    def on_task_complete(self, response):
        self.write("Completed!")
        self.finish()


class GenAsyncHandler(RequestHandler):
    @asynchronous
    @gen.engine
    def get(self):
        http_client = AsyncHTTPClient()
        response = yield gen.Task(http_client.fetch,
                            "http://localhost:8888/apply/tasks.sleep",
                            method="POST",
                            body=urlencode({"args": 3}))
        self.write(str(response.body))
        self.finish()


class GenMultipleAsyncHandler(RequestHandler):
    @asynchronous
    @gen.engine
    def get(self):
        http_client = AsyncHTTPClient()
        task1 = gen.Task(http_client.fetch,
                         "http://localhost:8888/apply/tasks.sleep",
                         method="POST",
                         body=urlencode({"args": 3})) 
        task2 = gen.Task(http_client.fetch,
                         "http://localhost:8888/apply/tasks.add",
                         method="POST",
                         body=urlencode({"args": [1, 2]})) 

        response1, response2 = yield [task1, task2]
        self.write(str(response1.body))
        self.finish()


application = Application([
    (r"/async-sleep", AsyncHandler),
    (r"/gen-async-sleep", GenAsyncHandler),
    (r"/gen-async-sleep-add", GenMultipleAsyncHandler),
])


if __name__ == "__main__":
    application.listen(8887)
    ioloop.IOLoop.instance().start()
