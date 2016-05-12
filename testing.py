#!flask/bin/python
import os
import unittest

from config import basedir
from app import app, db
from app.models import User, Post
from datetime import datetime, timedelta

class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_avatar(self):
        u = User(handle='john', email='john@example.com', social_id='foo_baring')
        avatar = u.avatar(128)
        expected = 'http://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6'
        assert avatar[0:len(expected)] == expected

    def test_make_unique_handle(self):
        u = User(handle='john', email='john@example.com', social_id='foo_baring')
        db.session.add(u)
        db.session.commit()
        handle = User.make_unique_handle('john')
        assert handle != 'john'
        u = User(handle=handle, email='susan@example.com', social_id='bunnyhops')
        db.session.add(u)
        db.session.commit()
        handle2 = User.make_unique_handle('john')
        assert handle2 != 'john'
        assert handle2 != handle

    def test_follow(self):
        u1 = User(handle='john', email='john@example.com', social_id='foo_baring')
        u2 = User(handle='susan', email='susan@example.com', social_id='lemmings')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        assert u1.unfollow(u2) is None
        u = u1.follow(u2)
        db.session.add(u)
        db.session.commit()
        assert u1.follow(u2) is None
        assert u1.is_following(u2)
        assert u1.followed.count() == 1
        assert u1.followed.first().handle == 'susan'
        assert u2.followers.count() == 1
        assert u2.followers.first().handle == 'john'
        u = u1.unfollow(u2)
        assert u is not None
        db.session.add(u)
        db.session.commit()
        assert not u1.is_following(u2)
        assert u1.followed.count() == 0
        assert u2.followers.count() == 0

    def test_follow_posts(self):
        # make four users
        u1 = User(handle='john', email='john@example.com', social_id='foo_baring')
        u2 = User(handle='susan', email='susan@example.com', social_id='fairly_hunky')
        u3 = User(handle='mary', email='mary@example.com', social_id='so_sad')
        u4 = User(handle='david', email='david@example.com', social_id='extra_tall')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)
        # make four posts
        utcnow = datetime.utcnow()
        p1 = Post(body="post from john", author=u1, timestamp=utcnow + timedelta(seconds=1))
        p2 = Post(body="post from susan", author=u2, timestamp=utcnow + timedelta(seconds=2))
        p3 = Post(body="post from mary", author=u3, timestamp=utcnow + timedelta(seconds=3))
        p4 = Post(body="post from david", author=u4, timestamp=utcnow + timedelta(seconds=4))
        db.session.add(p1)
        db.session.add(p2)
        db.session.add(p3)
        db.session.add(p4)
        db.session.commit()
        # u1 should follow everyone, and everyone them.
        for ninny in (User.query.all()):
            db.session.add(u1.follow(ninny))
            ninny.follow(u1)
            db.session.add(ninny)
        db.session.commit()
        # check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        assert len(f1) == 4
        assert len(f2) == 1
        assert len(f3) == 1
        assert len(f4) == 1
        assert f1 == [p4, p3, p2, p1]
        assert f2 == [p1]
        assert f4 == [p1]
        assert f3 == [p1]

if __name__ == '__main__':
    unittest.main()