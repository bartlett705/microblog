from app import app, db
from config import MAX_POST_LENGTH
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
from hashlib import md5
import flask.ext.whooshalchemy as whooshalchemy


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
	pic_url = db.Column(db.String(160))
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
		if self.pic_url != None:
			return self.pic_url
		else:
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
	__searchable__ = ['body']
 	id = db.Column(db.Integer, primary_key=True)
 	body = db.Column(db.String(MAX_POST_LENGTH))
 	timestamp = db.Column(db.DateTime)
 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

 	def __repr__(self):
 		return '<post %r>' % (self.body)

whooshalchemy.whoosh_index(app, Post)