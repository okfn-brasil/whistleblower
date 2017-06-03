import os

from celery import Celery

rabbitmq_url = os.environ.get('CLOUDAMQP_URL', 'pyamqp://guest@localhost//')
app = Celery('tasks', broker=rabbitmq_url)


@app.task
def add(x, y):
    return x + y


@app.task
def add(x, y):
    return x + y
