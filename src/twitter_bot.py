import os
import twitter

ACCESS_TOKEN_KEY = os.environ['TWITTER_ACCESS_TOKEN_KEY']
ACCESS_TOKEN_SECRET = os.environ['TWITTER_ACCESS_TOKEN_SECRET']
CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']
CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']

api = twitter.Api(consumer_key=CONSUMER_KEY,
                  consumer_secret=CONSUMER_SECRET,
                  access_token_key=ACCESS_TOKEN_KEY,
                  access_token_secret=ACCESS_TOKEN_SECRET)

def follow_congresspeople():
    accounts = pd.read_csv('twitter_accounts.csv')
    handlers = pd.concat([accounts['twitter_handle'],
                          accounts['secondary_twitter_handle']])
    for handler in handlers[handlers.notnull()].values:
        try:
            api.CreateFriendship(screen_name=handler)
        except Exception as e:
            print('{} handler not found'.format(handler))

def post(text):
    """Post an update to Twitter's timeline."""
    return api.PostUpdate(text)
