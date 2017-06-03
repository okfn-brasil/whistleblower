from unittest import TestCase, mock

import pandas as pd
from twitter import TwitterError

from whistleblower.targets.twitter import Post, Twitter


class TestTwitter(TestCase):

    def setUp(self):
        self.api = mock.MagicMock()
        self.subject = Twitter(api=self.api)

    def test_profiles(self):
        self.assertIsInstance(self.subject.profiles(), pd.DataFrame)

    def test_posted_reimbursements(self):
        database = mock.MagicMock()
        database.posts.find.return_value = [
            {'document_id': 10},
            {'document_id': 20},
            {'document_id': 30},
        ]
        subject = Twitter(database=database)
        ids = list(subject.posted_reimbursements())
        self.assertEqual([10, 20, 30], ids)

    @mock.patch('whistleblower.targets.twitter.logging')
    def test_follow_congresspeople(self, logging_mock):
        profiles = pd.DataFrame([
            ['DepEduardoCunha', 'DepEduardoCunha2'],
            ['DepRodrigomaia', None],
            [None, None]
        ], columns=['twitter_profile', 'secondary_twitter_profile'])
        self.subject.profiles = profiles
        calls = [
            mock.call.CreateFriendship(screen_name='DepEduardoCunha'),
            mock.call.CreateFriendship(screen_name='DepEduardoCunha2'),
            mock.call.CreateFriendship(screen_name='DepRodrigomaia'),
        ]
        self.subject.follow_congresspeople()
        self.api.assert_has_calls(calls, any_order=True)
        self.assertEqual(3, self.api.CreateFriendship.call_count)
        self.api.CreateFriendship.side_effect = TwitterError('Not found')
        self.subject.follow_congresspeople()
        logging_mock.warning.assert_called()
        self.assertEqual(3, logging_mock.warning.call_count)


class TestPost(TestCase):

    def setUp(self):
        self.api = mock.MagicMock()
        self.reimbursement = mock.MagicMock(
            congressperson_name='Eduardo Cunha',
            document_id=10,
            state_x='RJ',
            twitter_profile='DepEduardoCunha')
        self.subject = Post(self.reimbursement, api=self.api)

    def test_publish(self):
        self.subject.publish()
        self.api.PostUpdate.assert_called_once_with(self.subject.text())

    def test_text(self):
        message = (
            '🚨Gasto suspeito de Dep. @DepEduardoCunha (RJ). '
            'Você pode me ajudar a verificar? '
            'https://jarbas.serenatadeamor.org/#/documentId/10 #SerenataDeAmor'
        )
        self.assertEqual(message, self.subject.text())
        self.reimbursement.twitter_profile = None
        with self.assertRaises(ValueError):
            self.subject.text()
