import dateutil
import os
import re
import urllib.parse as urlparse
from urllib.parse import urlencode

import numpy as np
import pandas as pd
import requests
from pymongo import MongoClient

from whistleblower.suspicions import Suspicions

PAGE_ACCESS_TOKEN = os.environ['FACEBOOK_PAGE_ACCESS_TOKEN']
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://mongo:27017/')
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', 'whistleblower')

DATABASE = MongoClient(MONGO_URL)[MONGO_DATABASE]


class FacebookMessenger:
    """
    FacebookMessenger target.

    Maintains the logic for posting suspicious reimbursements
    as a Facebook Messenger bot.
    """

    def __init__(self, database=DATABASE):
        self.database = database

    def post_queue(self, reimbursements):
        """
        Given a list of reimbursements, return just those not yet posted.
        """
        rows = ~reimbursements.document_id.isin(self.posted_reimbursements())
        return reimbursements[rows]

    def posted_reimbursements(self):
        """
        List of document_id's already posted in the account.
        """
        results = self.database.posts.find({'target': 'facebook_messenger'},
                                           {'document_id': True})
        return np.r_[[post['document_id'] for post in results]]

    def provision_database(self):
        raise NotImplementedError

    def posts(self):
        raise NotImplementedError

    def __database_record_for_post(self, post):
        raise NotImplementedError


class Post:
    """
    Representation of a single reimbursement inside Facebook Messenger.
    """

    ENDPOINT = (
        'https://graph.facebook.com'
        '/v2.6/me/messages?access_token={}'
    ).format(PAGE_ACCESS_TOKEN)

    def __init__(self, reimbursement, database=DATABASE):
        self._profile_url = None
        self.database = database
        self.reimbursement = reimbursement

    def message(self):
        """
        Proper message for the given reimbursement.
        """
        subtitle = (
            'Verificou as informações do reembolso e concorda? '
            'Converse com o parlamentar.'
        )
        buttons = []
        if self.congressperson_page_url():
            buttons.append({
                'type': 'web_url',
                'url': self.congressperson_page_url(),
                'title': 'Página oficial',
            })
        if self.phone_number():
            buttons.append({
                'type': 'phone_number',
                'payload': self.phone_number(),
                'title': 'Ligar para gabinete',
            })
        buttons.append({'type': 'element_share'})
        return {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'image_aspect_ratio': 'square',
                    'elements': [{
                        'title': self.title(),
                        'image_url': self.picture_url(),
                        'subtitle': subtitle,
                        'default_action': {
                            'type': 'web_url',
                            'url': self.link(),
                        },
                        'buttons': buttons,
                    }]
                }
            }
        }

    def title(self):
        congressperson = self.reimbursement['congressperson_name_x'].title()
        return '🚨 Gasto suspeito de Dep. {} ({})'.format(
            congressperson, self.reimbursement['state_x'])

    def picture_url(self):
        if self._profile_url is None:
            url = self.congressperson_page_url().replace('www.', 'graph.')
            url_parts = list(urlparse.urlparse(url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query['fields'] = 'picture.type(large)'
            url_parts[4] = urlencode(query)
            request = requests.get(urlparse.urlunparse(url_parts))
            self._profile_url = request.json()['picture']['data']['url']
        return self._profile_url

    def link(self):
        return 'https://jarbas.serenatadeamor.org/#/documentId/{}'.format(
            self.reimbursement['document_id'])

    def congressperson_page_url(self):
        if self.reimbursement['facebook_page']:
            return self.reimbursement['facebook_page']

    def phone_number(self):
        if self.reimbursement['phone_number']:
            return '+55 (61) {}'.format(self.reimbursement['phone_number'])

    def publish(self):
        """
        Post the message to all available conversations.
        """
        for recipient in self.subscribers():
            self.publish_to_recipient(recipient)

    def subscribers(self):
        return ['1382735351782042']

    def publish_to_recipient(self, recipient):
        """
        Post the message to the conversation with the user.
        """
        payload = {'message': self.message(), 'recipient': {'id': recipient}}
        request = requests.post(self.ENDPOINT, json=payload)
        self.database.posts.insert_one(self.to_dict(request))

    def to_dict(self, request):
        """
        Dictionary representation to the post.
        """
        json_request = request.json()
        created_at = dateutil.parser.parse(request.headers['Date'][:-4])
        return {
            'created_at': created_at,
            'document_id': int(self.reimbursement['document_id']),
            'integration': 'chamber_of_deputies',
            'message_id': json_request['message_id'],
            'message': self.message(),
            'recipient_id': json_request['recipient_id'],
            'target': 'facebook_messenger',
        }
