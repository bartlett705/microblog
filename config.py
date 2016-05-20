import os

basedir = os.path.abspath(os.path.dirname(__file__))

# constants for our sqlite db
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# security schtuff
WTF_CSRF_ENABLED = True
SECRET_KEY = 'd0anlooktoohurd!'
OAUTH_CREDENTIALS = {
    'facebook': {
        'id': '264234120588822',
        'secret': '6d4ec14e7aefade958aa9013280d14d5'
    },
    'twitter': {
        'id': 'DjM3gJz0mfQ8HlywtRF8ZMmuD',
        'secret': '7IU007EloPTkfH0Lp6KPCV9BBNF1ckJePLiUsAdYTk2FJmzoQi'
    },
    'google' : {
    	'id' : "1068895437155-9qti0j2ft7kvhp5k5mrpvo69mlsk6mcm.apps.googleusercontent.com",
    	'secret' : "egKHqytF1dPVKlvVlL5jGoW5"
    }
}

#full-text search database
WHOOSH_BASE = os.path.join(basedir, 'search.db')

# Knobby constants
POSTS_PER_PAGE = 15
MAX_POST_LENGTH = 160
MAX_SEARCH_RESULTS = 50

# mail server settings
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USERNAME = None
MAIL_PASSWORD = None

# administrator list
ADMINS = ['lanceka@gmail.com']

#fun randomized messages, by category
MSG = {
	'confirm_post': [
	'Huh, really?  If you say so...',
	'I never would have guessed.',
	'That\'s one I won\'t forget anytime soon!',
	'Tell me more!'],
	'error' : [
	'Something Borked. Try elsewise.',
	'Sorry, come again? I was texting.',
	'Another Error. Sheesh, who programmed this thing?'],
	'hello' : [
	'Hey there, %s.',
	'Welcome to nowhere, %s.',
	'Oh hi, %s! Good to see you again.',
	'Well, well, well...if it isn\'t %s.'],
	'goodbye' : [
	'Bye-Bye.',
	'Tootles!',
	'Adios, amiga.',
	'See ya later!'],
	'inspiration': [
	'Take the path less traveled.',
	'What about Bob?',
	'Tell me a story.',
	'Where\'s Waldo?',
	'Give me a five-count.',
	'The secret to creativity is knowing how to hide your sources.',
	'yada, yada, yada',
	'blah, blah, blah',
	'Content goes *HERE*',]
}