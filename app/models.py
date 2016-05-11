from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    handle = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic') # backref creates an 'author' field in the post entries based on the linked user.id

    def __repr__(self):
        return '<User %r>' % (self.handle)

class Post(db.Model):
 	id = db.Column(db.Integer, primary_key=True)
 	body = db.Column(db.String(160))
 	timestamp = db.Column(db.DateTime)
 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

 	def __repr__(self):
 		return '<post %r>' % (self.body)
