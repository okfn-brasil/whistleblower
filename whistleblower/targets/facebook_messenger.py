import dateutil
import os
import re

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

    NAME = 'facebook_messenger'

    def __init__(self, database=DATABASE):
        self.database = database

    def subscribers(self):
        """
        List of Facebook users who chose to receive posts.
        """
        return [
            '1373004039480791',  # ana
            '1589086944459321',  # bruno
            '1382735351782042',  # cabral
            '1746654545349049',  # jessica
            '1739356122745392',  # tati
        ]


class Post:
    """
    Representation of a single reimbursement inside Facebook Messenger.
    """

    ENDPOINT = (
        'https://graph.facebook.com'
        '/v2.6/me/messages?access_token={}'
    ).format(PAGE_ACCESS_TOKEN)

    def __init__(self, reimbursement, database=DATABASE):
        self.database = database
        self.reimbursement = reimbursement
        self._profile_url = None

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
        """
        Title for the post.
        """
        congressperson = self.reimbursement['congressperson_name'].title()
        return '🚨 Gasto suspeito de Dep. {} ({})'.format(
            congressperson, self.reimbursement['state'])

    def picture_url(self):
        """
        Congressperson's picture URL.
        """
        return self.reimbursement['picture_url']

    def link(self):
        """
        URL to get more information about the reimbursement.
        """
        return 'https://jarbas.serenatadeamor.org/#/documentId/{}'.format(
            self.reimbursement['document_id'])

    def congressperson_page_url(self):
        """
        URL for congressperson's official Facebook representation.
        """
        if self.reimbursement['facebook_page']:
            return self.reimbursement['facebook_page']

    def phone_number(self):
        """
        Phone number to contact the congressperson.
        """
        if self.reimbursement['phone_number']:
            return '+55 (61) {}'.format(self.reimbursement['phone_number'])

    def publish(self):
        """
        Post the message to all available conversations.
        """
        for recipient in FacebookMessenger().subscribers():
            self.publish_to_recipient(recipient)

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
            'target': FacebookMessenger.NAME,
        }
