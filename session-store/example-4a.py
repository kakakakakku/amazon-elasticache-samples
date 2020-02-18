import os

import redis
from flask import Flask, session, redirect, escape, request

from datetime import datetime

# Configure the application name with the FLASK_APP environment variable.
app = Flask(__name__)


# Configure the secret_key with the SECRET_KEY environment variable.
app.secret_key = os.environ.get('SECRET_KEY', default=None)


# Configure the REDIS_URL constant with the REDIS_URL environment variable.
REDIS_URL = os.environ.get('REDIS_URL')


class SessionStore:
    """Store session data in Redis."""

    def __init__(self, token, url='redis://localhost:6379', ttl=100):
        self.token = token
        self.redis = redis.Redis.from_url(url, decode_responses=True)
        self.ttl = ttl

    def set(self, key, value):
        self.refresh()
        return self.redis.hset(self.token, key, value)

    def get(self, key):
        self.refresh()
        return self.redis.hget(self.token, key)

    def incr(self, key):
        self.refresh()
        return self.redis.hincrby(self.token, key, 1)

    def refresh(self):
        self.redis.expire(self.token, self.ttl)


@app.route('/')
def index():
    if 'username' in session:
        username = escape(session['username'])

        store = SessionStore(username, REDIS_URL)

        visits = store.incr('visits')

        return '''
            Logged in as {0}.<br>
            Visits: {1}<br>
            Last Access: {2}
        '''.format(username, visits, store.get('last_access'))

    return 'You are not logged in'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']

        store = SessionStore(session['username'], REDIS_URL)
        store.set('last_access', str(datetime.now()))

        return redirect('/')
    return '''
        <form method="post">
        <p><input type=text name=username>
        <p><input type=submit value=Login>
        </form>
    '''


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')
