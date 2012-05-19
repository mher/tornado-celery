from urlparse import urljoin

from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from tornado.escape import json_encode


class Task(gen.Task):
    def __init__(self, func, *args, **kwargs):
        self.http_client = AsyncHTTPClient()
        self.callback = kwargs.pop("callback", None)

        server = kwargs.pop("server", "http://localhost:8888")
        assert isinstance(func, basestring)
        self.url = urljoin(server, "apply/%s/" % func)

        super(Task, self).__init__(
                self.http_client.fetch, self.url, method="POST",
                body=json_encode({"args": args, "kwargs": kwargs}))

    def __call__(self, *args, **kwargs):
        assert self.callback
        return self.http_client.fetch(
                    self.url, self.callback, method="POST",
                    body=json_encode({"args": args, "kwargs": kwargs}))
