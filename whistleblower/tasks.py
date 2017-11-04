import json
import logging
import os
import subprocess

from celery import Celery
from celery.schedules import crontab

from whistleblower.targets.twitter import Post as TwitterPost
import whistleblower.queue

HOUR = 3600
ENABLED_TARGETS = [
    TwitterPost,
]
TWEET_HOUR_INTERVAL = int(os.environ.get('TWEET_HOUR_INTERVAL', '1'))
RABBITMQ_URL = os.environ.get('CLOUDAMQP_URL', 'pyamqp://guest@localhost//')
app = Celery('tasks', broker=RABBITMQ_URL)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    interval = TWEET_HOUR_INTERVAL * HOUR
    sender.add_periodic_task(interval, process_queue.s())


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
