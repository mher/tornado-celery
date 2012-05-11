import time

from celery import Celery

celery = Celery("tasks", broker="amqp://guest:guest@localhost:5672")
celery.conf.CELERY_RESULT_BACKEND = "amqp"


@celery.task
def add(x, y):
    return int(x) + int(y)


@celery.task
def sleep(seconds):
    time.sleep(float(seconds))
    return seconds 


@celery.task
def echo(msg):
    return msg


@celery.task
def error(msg):
    raise Exception(msg)


if __name__ == "__main__":
    celery.start()
