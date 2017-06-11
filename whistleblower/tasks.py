import json
import logging
import os

from celery import Celery
from celery.schedules import crontab

from whistleblower.suspicions import Suspicions
from whistleblower.targets.twitter import Post as TwitterPost, Twitter

rabbitmq_url = os.environ.get('CLOUDAMQP_URL', 'pyamqp://guest@localhost//')
app = Celery('tasks', broker=rabbitmq_url)


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
