import logging
import os

import numpy as np
import pandas as pd
from pymongo import MongoClient
import twitter

ACCESS_TOKEN_KEY = os.environ['TWITTER_ACCESS_TOKEN_KEY']
ACCESS_TOKEN_SECRET = os.environ['TWITTER_ACCESS_TOKEN_SECRET']
CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']
CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']

API = twitter.Api(consumer_key=CONSUMER_KEY,
                  consumer_secret=CONSUMER_SECRET,
                  access_token_key=ACCESS_TOKEN_KEY,
                  access_token_secret=ACCESS_TOKEN_SECRET)
DATABASE = MongoClient('mongodb://mongo:27017/')['whistleblower']
PROFILES_FILE = 'data/twitter_profiles.csv'


class Twitter:
    """
    Twitter target.

    Maintains the logic for posting suspicious reimbursements
    in a Twitter account.
    """

    def __init__(self, api=API, database=DATABASE, profiles_file=PROFILES_FILE):
        self.api = api
        self.database = database
        self.profiles_file = profiles_file
        self._profiles = None

    def profiles(self):
        """
        Dataframe with congresspeople profiles to be mentioned in posts.
        """
        if self._profiles is None:
            self._profiles = pd.read_csv(self.profiles_file)
        return self._profiles

    def posted_reimbursements(self):
        """
        List of document_id's already posted in the account.
        """
        results = self.database.posts.find({'target': 'twitter'},
                                           {'document_id': True})
        return np.r_[[post['document_id'] for post in results]]

    def follow_congresspeople(self):
        """
        Friend all congresspeople accounts on Twitter.
        """
        profiles = pd.concat([self.profiles['twitter_profile'],
                              self.profiles['secondary_twitter_profile']])
        for profile in profiles[profiles.notnull()].values:
            try:
                self.api.CreateFriendship(screen_name=profile)
            except twitter.TwitterError:
                logging.warning('{} profile not found'.format(profile))


class Post:
    """
    Representation of a single reimbursement inside Twitter.
    """

    def __init__(self, reimbursement, api=API):
        self.api = api
        self.reimbursement = reimbursement

    def text(self):
        """
        Proper tweet message for the given reimbursement.
        """
        profile = self.reimbursement.twitter_profile
        if profile:
            link = 'https://jarbas.serenatadeamor.org/#/documentId/{}'.format(
                self.reimbursement.document_id)
            message = (
                '🚨Gasto suspeito de Dep. @{} ({}). '
                'Você pode me ajudar a verificar? '
                '{} #SerenataDeAmor'
            ).format(profile, self.reimbursement.state_x, link)
            return message
        else:
            raise ValueError(
                'Congressperson does not have a registered Twitter account.')

    def publish(self):
        """
        Post the update to Twitter's timeline.
        """
        return self.api.PostUpdate(self.text())
