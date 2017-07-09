import json
import os

from pymongo import MongoClient

from .suspicions import Suspicions
from .targets.twitter import Twitter
import whistleblower.tasks

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://mongo:27017/')
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', 'whistleblower')
DATABASE = MongoClient(MONGO_URL)[MONGO_DATABASE]


class Queue:

    def __init__(self, database=DATABASE):
        self.database = database
        self._reimbursements = None

    def update(self):
        """
        Ensure a uniqueness index exists on the `document_id` field before
        inserting remaining_posts.
        """
        self.database.queue.delete_many({})
        self.database.queue.create_index('document_id', unique=True)
        self.database.queue.insert_many(list(self.remaining_posts()),
                                        ordered=False)

    def process(self):
        """
        Fetch a record from the queue, trigger its publication and deletes it.
        """
        record = self.database.queue.find_one_and_delete({})
        whistleblower.tasks.publish_reimbursement(record)

    def remaining_posts(self):
        """
        Iterable containing the reimbursements not yet posted on Twitter,
        in a random order.
        """
        queue = Twitter().post_queue(self.reimbursements()).sample(frac=1)
        for _, post in queue.iterrows():
            yield json.loads(post.to_json())

    def reimbursements(self):
        """
        Dataframe with all available reimbursements.
        """
        if self._reimbursements is None:
            self._reimbursements = Suspicions().all()
        return self._reimbursements
