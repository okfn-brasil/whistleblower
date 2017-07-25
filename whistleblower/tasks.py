import json
import logging
import os
import subprocess

from celery import Celery
from celery.schedules import crontab

from .targets.twitter import Post as TwitterPost
import whistleblower.queue

HOUR = 3600
ENABLED_TARGETS = [
    TwitterPost,
]
RABBITMQ_URL = os.environ.get('CLOUDAMQP_URL', 'pyamqp://guest@localhost//')
app = Celery('tasks', broker=RABBITMQ_URL)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(4 * HOUR, process_queue.s())


@app.task
def update_queue():
    whistleblower.queue.Queue().update()


@app.task
def process_queue():
    whistleblower.queue.Queue().process()


@app.task
def publish_reimbursement(reimbursement):
    for target in ENABLED_TARGETS:
        target(reimbursement).publish()
