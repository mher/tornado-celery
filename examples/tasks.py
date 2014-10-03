import os
import time
from datetime import datetime

from celery import Celery

celery = Celery("tasks", broker="amqp://guest:guest@localhost:5672")
celery.conf.CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'amqp')


@celery.task(name='tasks.add')
def add(x, y):
    return int(x) + int(y)


@celery.task(name='tasks.sleep')
def sleep(seconds):
    time.sleep(float(seconds))
    return seconds


@celery.task(name='tasks.echo')
def echo(msg, timestamp=False):
    print "echooooo"
    return "%s: %s" % (datetime.now(), msg) if timestamp else msg


@celery.task(name='tasks.error')
def error(msg):
    raise Exception(msg)


if __name__ == "__main__":
    celery.start()
