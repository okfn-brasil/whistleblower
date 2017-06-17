import json
import logging
import os
import subprocess

from celery import Celery
from celery.schedules import crontab

from whistleblower.suspicions import Suspicions
from whistleblower.targets.twitter import Post as TwitterPost, Twitter

rabbitmq_url = os.environ.get('CLOUDAMQP_URL', 'pyamqp://guest@localhost//')
app = Celery('tasks', broker=rabbitmq_url)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=3),
        update_suspicions_dataset.s()
    )
    sender.add_periodic_task(
        crontab(hour=13),
        enqueue_twitter_posts.s()
    )


@app.task
def update_suspicions_dataset():
    subprocess.run(['python', 'whistleblower/get_dataset.py'], check=True)
    subprocess.run(['python', 'rosie/rosie.py', 'run',
                    'chamber_of_deputies', 'data'], check=True)


@app.task
def enqueue_twitter_posts():
    reimbursements = Suspicions().all()
    queue = Twitter().post_queue(reimbursements)
    logging.info('Queue for Twitter: {} reimbursements'.format(len(queue)))
    sample = queue.sample(4)
    for index in range(0, 4):
        reimbursement = json.loads(sample.iloc[index].to_json())
        delay = index * 4 * 3600
        post_reimbursement_to_twitter.apply_async([reimbursement],
                                                  countdown=delay)


@app.task
def post_reimbursement_to_twitter(reimbursement):
    post = TwitterPost(reimbursement)
    post.publish()
