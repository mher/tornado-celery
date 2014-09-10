import time
from datetime import datetime

from celery import Celery

celery = Celery("redis_tasks", broker="amqp://guest:guest@localhost:5672")
celery.conf.CELERY_RESULT_BACKEND = 'redis://'


@celery.task(name="redis_tasks.add")
def add(x, y):
    return int(x) + int(y)


@celery.task(name="redis_tasks.sleep")
def sleep(seconds):
    time.sleep(float(seconds))
    return seconds


@celery.task(name="redis_tasks.echo")
def echo(msg, timestamp=False):
    return "%s: %s" % (datetime.now(), msg) if timestamp else msg


@celery.task(name="redis_tasks.error")
def error(msg):
    raise Exception(msg)


if __name__ == "__main__":
    celery.start()
