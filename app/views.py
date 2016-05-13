# define views
from datetime import datetime
from random import choice
from flask import render_template, flash, redirect, url_for, request, session, g
from forms import EditForm, PostForm
from app import app, db, lm
from models import User, Post
from flask_oauthlib.client import OAuth
from flask.ext.login import login_user, logout_user, current_user, login_required

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

oauth = OAuth()
fb_oauth = oauth.remote_app('facebook',
        base_url='https://graph.facebook.com/',
        request_token_url=None,
        access_token_url='/oauth/access_token',
        authorize_url='https://www.facebook.com/dialog/oauth',
        consumer_key=app.config['OAUTH_CREDENTIALS']['facebook']['id'],
        consumer_secret=app.config['OAUTH_CREDENTIALS']['facebook']['secret'],
        request_token_params={'scope': 'email'})

@fb_oauth.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
def index(page=1):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash(choice(app.config['MSG']['confirm_post']))
        return redirect(url_for('index'))
    posts = g.user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
    return render_template('index.html', title='Home', user=g.user, form=form, posts=posts, max_post_length=app.config['MAX_POST_LENGTH'])

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

@app.route('/login')
def login():
    if current_user.is_authenticated:
        flash('You\'re already logged in, silly!')
        return redirect(url_for('index'))
    else:
        return render_template('login.html',
                           title='Validate Credentials')

@app.route('/authorize/facebook')
def oauth_authorize_fb():
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    return fb_oauth.authorize(callback='http://kanawi-dev.heroku.com:5000/callback/facebook')

@app.route('/callback/facebook')
@fb_oauth.authorized_handler
def oauth_callback_fb(resp):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    session['facebook_token'] = (resp['access_token'], '')
    data = fb_oauth.get('/me?fields=name,email').data
    print data
    social_id = '$facebook:' + data['id']
    handle = data['name']
    if 'email' in data:
        email = data['email']
    else:
        email = 'insufficient_permission'
    if social_id is None:
        flash(choice(app.config['MSG']['error']))
        return redirect(request.args.get('next') or url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    flash(choice(app.config['MSG']['hello']) % handle)
    if not user:
        user = User(social_id=social_id, handle=handle, email=email)
        db.session.add(user)
        db.session.commit()
        for ninny in (User.query.all()):
            db.session.add(user.follow(ninny))
            ninny.follow(user)
            db.session.add(ninny)
            db.session.commit()
        flash('Welcome to the party!')
    login_user(user, True)
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    flash (choice(app.config['MSG']['goodbye']))
    return redirect(url_for('index'))

@app.route('/user/<handle>/<int:page>')
@login_required
def user(handle, page=1):
    user = User.query.filter_by(handle=handle).first()
    if user == None:
        flash('No idea who %s is.' % handle)
        return redirect(url_for('index'))
    posts = user.posts.paginate(page, app.config['POSTS_PER_PAGE'], False)
    return render_template('user.html',
                           user=user,
                           posts=posts)

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.handle)
    if form.validate_on_submit():
        g.user.handle = form.handle.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash(choice(app.config['MSG']['confirm_post']))
        return redirect(url_for('edit'))
    else:
        form.handle.data = g.user.handle
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)

@app.route('/follow/<handle>')
@login_required
def follow(handle):
    user = User.query.filter_by(handle=handle).first()
    if user is None:
        flash ("We don't know any %s." % handle)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You are already following yourself, silly!')
        return redirect(url_for('user', handle=handle, page=1))
    new_u = g.user.follow(user)
    if new_u is None:
        flash("A magical barrier prevents you from following %s." % handle)
        return redirect(url_for('user', handle=handle, page=1))
    db.session.add(new_u)
    db.session.commit()
    flash('Sucesfully followed %s.' % handle)
    return redirect(url_for('user', handle=handle, page=1))

@app.route('/unfollow/<handle>')
@login_required
def unfollow(handle):
    user = User.query.filter_by(handle=handle).first()
    if user is None:
        flash('I have no idea who %s is, so don\'t worry, you won\'t hear from them.' % handle)
        return redirect(url_for('index'))
    if user == g.user:
        flash('Yeah, right. If you learn how to un-follow yourself, let me know!')
        return redirect(url_for('user', handle=handle))
    u = g.user.unfollow(user)
    if u is None:
        flash('That\'s weird, you can\'t unfollow ' + handle + '.')
        return redirect(url_for('user', handle=handle))
    db.session.add(u)
    db.session.commit()
    flash('You have  ' + handle + '.')
    return redirect(url_for('user', handle=handle))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500