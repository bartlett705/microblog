from app import db
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
from hashlib import md5


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	handle = db.Column(db.String(64), nullable=False, index=True, unique=True)
	email = db.Column(db.String(64), index=True, unique=True)
	social_id = db.Column(db.String(64), nullable=False, unique=True)
	posts = db.relationship('Post', backref='author', lazy='dynamic') # backref creates an 'author' field in the post entries based on the linked user.id
	about_me = db.Column(db.String(260))
	last_seen = db.Column(db.DateTime)
	followed = db.relationship('User',
		secondary=followers,
		primaryjoin=(followers.c.follower_id == id),
		secondaryjoin=(followers.c.followed_id == id),
		backref=db.backref('followers', lazy='dynamic'),
		lazy='dynamic')

	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)
			return self

	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)
			return self

	def is_following(self, user):
		return self.followed.filter(followers.c.followed_id == user.id).count() > 0

	def followed_posts(self):
		return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc())
	
	def avatar(self, size):
		return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)

	@staticmethod # handle nickname collisions by adding an int to make it unique
	def make_unique_handle(handle):
		if User.query.filter_by(handle=handle).first() is None:
			return handle
		version = 2
		while True:
			new_handle = handle + str(version)
			if User.query.filter_by(handle=new_handle).first() is None:
				break
			version += 1
		return new_handle

	@property
	def is_authenticated(self): #The next four function are for flask-login's sake
		return True
	@property
	def is_active(self):
		return True
	@property
	def is_anonymous(self):
		return False
	def get_id(self):
		return unicode(self.id)  # python 2
	def __repr__(self):
		return '<User %r>' % (self.handle)

class Post(db.Model):
 	id = db.Column(db.Integer, primary_key=True)
 	body = db.Column(db.String(160))
 	timestamp = db.Column(db.DateTime)
 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

 	def __repr__(self):
 		return '<post %r>' % (self.body)


# class OAuthSignIn(object):
#     providers = None

#     def __init__(self, provider_name):
#         self.provider_name = provider_name
#         credentials = app.config['OAUTH_CREDENTIALS'][provider_name]
#         self.consumer_id = credentials['id']
#         self.consumer_secret = credentials['secret']

#     def authorize(self):
#         pass

#     def callback(self):
#         pass

#     def get_callback_url(self):
#         return url_for('oauth_callback', provider=self.provider_name,
#                        _external=True)

#     @classmethod
#     def get_provider(self, provider_name):
#         if self.providers is None:
#             self.providers = {}
#             for provider_class in self.__subclasses__():
#                 provider = provider_class()
#                 self.providers[provider.provider_name] = provider
#         return self.providers[provider_name]

# class TwitterSignIn(OAuthSignIn):
#     def __init__(self):
#         super(TwitterSignIn, self).__init__('twitter')
#         auther = OAuth()
#         self.service = auther.remote_app('twitter', base_url='https://api.twitter.com/1/', request_token_url='https://api.twitter.com/oauth/request_token', access_token_url='https://api.twitter.com/oauth/access_token', authorize_url='https://api.twitter.com/oauth/authorize', consumer_key=self.consumer_id, consumer_secret=self.consumer_secret)

# 	def authorize(self):
# 		return self.service.authorize(callback=url_for('oauth_callback', next=request.args.get('next') or request.referrer or None))

#     def callback(self):
#     	resp = self.service.authorized_response()
#         social_id = 'twitter$' + str(resp.get('id'))
#         username = resp.get('screen_name')
#         session['twitter_token'] = (resp['oauth_token'], resp['oauth_token_secret'])
#     	flash('You were signed in as %s' % resp['screen_name'])
#         return social_id, username, None   # Twitter does not provide email

# 	def get_twitter_token(token=None):
# 	    	return session.get('twitter_token')