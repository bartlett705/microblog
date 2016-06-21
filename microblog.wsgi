#!/usr/bin/python
import os, sys
import logging
from flipflop import WSGIServer
logging.basicConfig(stream=sys.stderr)
sys.path.append(os.path.dirname(__file__))
sys.path.append("/var/www/microblog/flask/lib/python2.7/site-packages")
os.environ['DATABASE_URL'] = 'mysql://apps:sweethunty@localhost/apps'

from app import app as application
application.secret_key = 'sweethunty'
if __name__ == '__main__':
	WSGIServer(application).run()
