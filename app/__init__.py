from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from config import basedir #, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD
from flask.ext.misaka import Misaka
#from flask_emoji import Emoji

app = Flask(__name__)
app.config.from_object('app.config')
db = SQLAlchemy(app)
lm = LoginManager(app)
lm.init_app(app)
lm.login_view = 'login'
misaka = Misaka(html=True, smartypants=True, highlight=True, no_intra_emphasis=True, strikethrough=True, superscript=True)
misaka.init_app(app)
#emoji = Emoji(app)

# if not app.debug: # to run a debug server: python -m smtpd -n -c DebuggingServer localhost:25
#     import logging
#     from logging.handlers import SMTPHandler
    # credentials = None
    # if MAIL_USERNAME or MAIL_PASSWORD:
    #     credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    # mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@' + MAIL_SERVER, ADMINS, 'microblog failure', credentials)
    # mail_handler.setLevel(logging.ERROR)
    # app.logger.addHandler(mail_handler)

from .momentjs import momentjs
app.jinja_env.globals['momentjs'] = momentjs

import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger('microblog')
file_handler = RotatingFileHandler('tmp/microblog.log', 'a', 1 * 1024 * 1024, 10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: [in %(pathname)s:%(lineno)d] %(message)s'))
logger.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.info('microblog startup')

from app import views, models

if __name__ == "__main__":
	app.run()










