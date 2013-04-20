from __future__ import absolute_import
from __future__ import with_statement

import celery


class AsyncResult(celery.result.AsyncResult):
    def __init__(self, task_id, status=None, traceback=None, result=None,
                 **kwargs):
        super(AsyncResult, self).__init__(task_id)
        self._status = status
        self._traceback = traceback
        self._result = result

    @property
    def status(self):
        return self._status or super(AsyncResult, self).status
    state = status

    @property
    def traceback(self):
        if self._result is not None:
            return self._traceback
        else:
            return super(AsyncResult, self).traceback

    @property
    def result(self):
        return self._result or super(AsyncResult, self).result
