import datetime
from unittest import TestCase, mock, skip

from whistleblower.targets.facebook_messenger import Post, FacebookMessenger


class TestFacebookMessenger(TestCase):

    def setUp(self):
        self.database = mock.MagicMock()
        self.subject = FacebookMessenger(database=self.database)

    @skip('Not properly implemented yet')
    def test_subscribers(self):
        pass


class TestPost(TestCase):

    def setUp(self):
        self.database = mock.MagicMock()
        self.reimbursement = {
            'congressperson_name': 'EDUARDO CUNHA',
            'document_id': 10,
            'facebook_page': 'https://www.facebook.com/DeputadoEduardoCunha',
            'phone_number': '3040-5060',
            'picture_url': 'http://www.camara.gov.br/internet/deputado/bandep/74173.jpg',
            'state': 'RJ',
        }
        self.subject = Post(self.reimbursement, database=self.database)
        self.request = mock.MagicMock()
        self.request.headers = {'Date': 'Sun, 09 Jul 2017 12:41:22 GMT'}
        self.request.json.return_value = {'message_id': 123, 'recipient_id': 987}

    def test_message(self):
        message = {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'image_aspect_ratio': 'square',
                    'elements': [{
                        'title': '🚨 Gasto suspeito de Dep. Eduardo Cunha (RJ)',
                        'image_url': 'http://www.camara.gov.br/internet/deputado/bandep/74173.jpg',
                        'subtitle': 'Verificou as informações do reembolso e concorda? Converse com o parlamentar.',
                        'default_action': {
                            'type': 'web_url',
                            'url': 'https://jarbas.serenatadeamor.org/#/documentId/10',
                        },
                        'buttons': [
                            {
                                'type': 'web_url',
                                'url': 'https://www.facebook.com/DeputadoEduardoCunha',
                                'title': 'Página oficial',
                            },
                            {
                                'type': 'phone_number',
                                'payload': '+55 (61) 3040-5060',
                                'title': 'Ligar para gabinete',
                            },
                            {
                                'type': 'element_share',
                            }
                        ]
                    }]
                }
            }
        }
        self.assertEqual(message, self.subject.message())

    def test_title(self):
        self.assertEqual('🚨 Gasto suspeito de Dep. Eduardo Cunha (RJ)',
                         self.subject.title())

    def test_picture_url(self):
        self.assertEqual('http://www.camara.gov.br/internet/deputado/bandep/74173.jpg',
                         self.subject.picture_url())

    def test_link(self):
        self.assertEqual('https://jarbas.serenatadeamor.org/#/documentId/10',
                         self.subject.link())

    def test_congressperson_page_url(self):
        self.assertEqual('https://www.facebook.com/DeputadoEduardoCunha',
                         self.subject.congressperson_page_url())
        self.reimbursement['facebook_page'] = None
        self.assertEqual(None, self.subject.congressperson_page_url())

    def test_phone_number(self):
        self.assertEqual('+55 (61) 3040-5060',
                         self.subject.phone_number())
        self.reimbursement['phone_number'] = None
        self.assertEqual(None, self.subject.phone_number())

    @mock.patch('whistleblower.targets.facebook_messenger.requests')
    def test_publish_to_recipient(self, requests_mock):
        requests_mock.post.return_value = self.request
        self.subject.publish_to_recipient(987)
        self.database.posts.insert_one.assert_called_once_with(
            self.subject.to_dict(self.request))
        payload = {'message': self.subject.message(), 'recipient': {'id': 987}}
        calls = [mock.call.post(self.subject.ENDPOINT, json=payload)]
        requests_mock.assert_has_calls(calls)

    def test_to_dict(self):
        response = {
            'created_at': datetime.datetime(2017, 7, 9, 12, 41, 22),
            'document_id': self.reimbursement['document_id'],
            'integration': 'chamber_of_deputies',
            'message_id': 123,
            'message': self.subject.message(),
            'recipient_id': 987,
            'target': 'facebook_messenger',
        }
        self.assertEqual(response, self.subject.to_dict(self.request))
