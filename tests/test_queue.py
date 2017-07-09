from unittest import TestCase, mock

import pandas as pd

from whistleblower.queue import Queue as subject_class


class TestQueue(TestCase):
    def setUp(self):
        self.database = mock.MagicMock()
        self.subject = subject_class(self.database)

    @mock.patch('whistleblower.queue.Suspicions')
    @mock.patch('whistleblower.queue.Twitter')
    def test_update(self, twitter_mock, suspicions_mock):
        suspicions = pd.DataFrame([pd.Series({'document_id': 1})])
        twitter_mock.return_value.post_queue.return_value.sample.return_value = suspicions
        self.subject.update()
        self.database.queue.delete_many.assert_called_once_with({})
        self.database.queue.create_index.assert_called_once_with('document_id', unique=True)
        self.database.queue.insert_many.assert_called_once_with(
            list(self.subject.remaining_posts()), ordered=False)

    @mock.patch('whistleblower.queue.whistleblower.tasks.publish_reimbursement')
    def test_process(self, publish_reimbursement_mock):
        reimbursement = {'document_id': 10}
        self.database.queue.find_one_and_delete.return_value = reimbursement
        self.subject.process()
        publish_reimbursement_mock.assert_called_once_with(reimbursement)

    @mock.patch('whistleblower.queue.Suspicions')
    @mock.patch('whistleblower.queue.Twitter')
    def test_remaining_posts(self, twitter_mock, suspicions_mock):
        suspicions = pd.DataFrame([pd.Series({'document_id': i}) for i in range(1, 5)])
        suspicions_mock.return_value.all.return_value = suspicions
        twitter_mock.return_value.post_queue.return_value.sample.return_value = suspicions.head(2)
        response = [post for post in self.subject.remaining_posts()]
        self.assertEqual(suspicions.iloc[0].to_dict(), response[0])
        self.assertEqual(suspicions.iloc[1].to_dict(), response[1])

    @mock.patch('whistleblower.queue.Suspicions')
    def test_reimbursements(self, suspicions_mock):
        suspicions = [{'document_id': 10}]
        suspicions_mock.return_value.all.return_value = suspicions
        self.assertEqual(suspicions, self.subject.reimbursements())
