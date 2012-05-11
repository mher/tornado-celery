from __future__ import absolute_import

import sys
import time

from functools import partial
from urllib import urlencode

import requests

from tornado import ioloop
from tornado import httpclient


echo_url = "http://localhost:8888/apply/tasks.echo/"
async_echo_url = "http://localhost:8888/async-apply/tasks.echo/"


def _timeit_fetch(url, ntimes):
    time_start = time.time()
    def done(response, n):
        if n==ntimes-1:
            ioloop.IOLoop.instance().stop()

    http_client = httpclient.AsyncHTTPClient()
    for i in range(ntimes):
        http_client.fetch(url, partial(done, n=i), method="POST", 
                          body=urlencode({"args": i}))
    ioloop.IOLoop.instance().start()
    return ntimes, time.time() - time_start


def bench_apply(ntimes):
    print("apply %d times: %ss" % _timeit_fetch(echo_url, ntimes))


def bench_async_apply(ntimes):
    print("async-apply %d times: %ss" % _timeit_fetch(async_echo_url, ntimes))


def bench_async_apply_with_requests(ntimes):
    time_start = time.time()
    for i in range(ntimes):
        requests.post(async_echo_url, data={"args":"foo"})
    print("async-apply-with-requests %d times: %ss" % (ntimes, time.time() - time_start))


def bench_delay(ntimes):
    from examples.tasks import echo
    time_start = time.time()
    for i in range(ntimes):
        echo.delay(i)
    print("delay %d times: %ss" % (ntimes, time.time() - time_start))


if __name__=="__main__":
    ntimes = int(sys.argv[1]) if len(sys.argv)>1 else 100
    method = sys.argv[2] if len(sys.argv)==3 else None
    if method:
        vars()[method](ntimes)
    else:
        bench_delay(ntimes)
        bench_async_apply_with_requests(ntimes)
        bench_async_apply(ntimes)
        bench_apply(ntimes)
