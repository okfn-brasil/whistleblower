import http.client
import os

from flask import Flask
from pymongo import MongoClient

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://mongo:27017/')
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', 'whistleblower')
DATABASE = MongoClient(MONGO_URL)[MONGO_DATABASE]
app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/facebook_webhook', methods=['POST'])
def facebook_webhook():
    DATABASE.facebook_webhook.insert(request.form)
    return ('', http.client.NO_CONTENT)
