import os

import pandas as pd
import twitter

ACCESS_TOKEN_KEY = os.environ['TWITTER_ACCESS_TOKEN_KEY']
ACCESS_TOKEN_SECRET = os.environ['TWITTER_ACCESS_TOKEN_SECRET']
CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']
CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
API = twitter.Api(consumer_key=CONSUMER_KEY,
                  consumer_secret=CONSUMER_SECRET,
                  access_token_key=ACCESS_TOKEN_KEY,
                  access_token_secret=ACCESS_TOKEN_SECRET)

ACCOUNTS = pd.read_csv('data/twitter_accounts.csv')


def follow_congresspeople():
    handlers = pd.concat([ACCOUNTS['twitter_handle'],
                          ACCOUNTS['secondary_twitter_handle']])
        for handler in handlers[handlers.notnull()].values:
        try:
            API.CreateFriendship(screen_name=handler)
        except Exception as e:
            print('{} handle not found'.format(handler))


def handle_for_reimbursement(reimbursement):
    name = reimbursement['congressperson_name']
    query = 'congressperson == "{}"'.format(name)
    return ACCOUNTS.query(query)['twitter_handle'].values[0]


def post_reimbursement(reimbursement):
    handle = handle_for_reimbursement(reimbursement)
    if handle:
        link = 'https://jarbas.serenatadeamor.org/#/documentId/{}'.format(
            reimbursement['document_id'])
        message = (
            '🚨Gasto suspeito de Dep. @{}. '
            'Você pode me ajudar a verificar? '
            '{} #SerenataDeAmor'
        ).format(handle, link)
    else:
        raise ValueError('Congressperson does not have a registered Twitter account.')


def post(text):
    """Post an update to Twitter's timeline."""
    return API.PostUpdate(text)
