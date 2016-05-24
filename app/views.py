# define views
from datetime import datetime
from random import choice
from json import loads
from flask import render_template, flash, redirect, url_for, request, session, g
from forms import EditUserForm, PostForm, SearchForm, EditPostForm
from app import app, db, lm
from models import User, Post
from flask_oauthlib.client import OAuth
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.misaka import markdown

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
        request_token_params={'scope': 'email, public_profile'})

tw_oauth = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authorize',
    consumer_key=app.config['OAUTH_CREDENTIALS']['twitter']['id'],
    consumer_secret=app.config['OAUTH_CREDENTIALS']['twitter']['secret']
)

gg_oauth = oauth.remote_app('google',
                          base_url='https://www.google.com/accounts/',
                          authorize_url='https://accounts.google.com/o/oauth2/auth',
                          request_token_url=None,
                          request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email'},
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          access_token_method='POST',
 #                         access_token_params={'grant_type': 'authorization_code'},
                          consumer_key=app.config['OAUTH_CREDENTIALS']['google']['id'],
                          consumer_secret=app.config['OAUTH_CREDENTIALS']['google']['secret'])

@fb_oauth.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

@tw_oauth.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')

@gg_oauth.tokengetter
def get_access_token():
    return session.get('google_token')

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
    return render_template('index.html', title='Home', user=g.user, form=form, posts=posts, max_post_length=app.config['MAX_POST_LENGTH'], inspiration=choice(app.config['MSG']['inspiration']))

@app.route('/search', methods=['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query=g.search_form.search.data))

@app.route('/search_results/<query>')
@login_required
def search_results(query):
    results = Post.query.whoosh_search(query, app.config['MAX_SEARCH_RESULTS']).all()
    return render_template("search_results.html", user=g.user, query=query, results=results)


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()

@app.route('/login')
def login():
    if current_user.is_authenticated:
        flash('You\'re already logged in.')
        return redirect(url_for('index'))
    else:
        return render_template('login.html',
                           title='Validate Credentials')

@app.route('/authorize/facebook')
def oauth_authorize_fb():
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    return fb_oauth.authorize(callback='http://kanawi-dev.heroku.com:5000/callback/facebook', next=request.args.get('next') or request.referrer or None)

@app.route('/callback/facebook')
@fb_oauth.authorized_handler
def oauth_callback_fb(resp):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash('It looks like you said no.')
        return redirect(next_url)
    session['facebook_token'] = (resp['access_token'], '')
    data = fb_oauth.get('/me?fields=name,email,picture').data
    social_id = '$facebook:' + data['id']
    handle = data['name']
    if 'email' in data:
        email = data['email']
    else:
        email = 'insufficient_permission'
    if 'picture' in data:
        pic_url = data['picture']['data']['url']
    else:
        pic_url = None
    validate_user(social_id, handle, email, pic_url)
    return redirect(url_for('index'))

@app.route('/authorize/twitter')
def oauth_authorize_tw():
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    return tw_oauth.authorize(callback=url_for('oauth_callback_tw', next=request.args.get('next') or request.referrer or None))

@app.route('/callback/twitter')
@tw_oauth.authorized_handler
def oauth_callback_tw(resp):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash('Looks like you said no.')
        return redirect(next_url)
    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    handle = resp['screen_name']
    social_id = '$twitter:' + resp['user_id']
    email = 'twitter user'
    validate_user(social_id, handle, email)
    return redirect(url_for('index'))

@app.route('/authorize/google')
def oauth_authorize_gg():
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    callback=url_for('oauth_callback_gg', _external=True)
    return gg_oauth.authorize(callback=callback)

@app.route('/callback/google')
@gg_oauth.authorized_handler
def oauth_callback_gg(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash('Looks like you said no.')
        return redirect(next_url)
    access_token = resp['access_token']
    session['google_token'] = access_token, ''
    from urllib2 import Request, urlopen, URLError
 
    headers = {'Authorization': 'OAuth '+access_token}
    req = Request('https://www.googleapis.com/oauth2/v1/userinfo',
                  None, headers)
    try:
        res = urlopen(req)
    except URLError, e:
        if e.code == 401:
            # Unauthorized - bad token
            session.pop('access_token', None)
            return redirect(url_for('login'))
    data = loads(res.read())
    handle = data['name']
    social_id = '$google:' + data['id']
    email = data['email']
    pic_url = data['picture']
    validate_user(social_id, handle, email, pic_url)
    return redirect(url_for('index'))


def validate_user(social_id, handle, email, pic_url=''):
    if social_id is None:
        flash(choice(app.config['MSG']['error']))
        return redirect(request.args.get('next') or url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    flash(choice(app.config['MSG']['hello']) % handle)
    if not user:
        user = User(social_id=social_id, handle=handle, email=email, pic_url=pic_url)
        db.session.add(user)
        db.session.commit()
        for ninny in (User.query.all()): #New users start out following everyone, and get auto-followed by existing users.
            db.session.add(user.follow(ninny))
            ninny.follow(user)
            db.session.add(ninny)
            db.session.commit()
        flash('Welcome to the party!')
    login_user(user, True)


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
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    return render_template('user.html',
                           user=user,
                           posts=posts)

@app.route('/edit_user', methods=['GET', 'POST'])
@login_required
def edit_user():
    form = EditUserForm(g.user.handle)
    if form.validate_on_submit():
        g.user.handle = form.handle.data
        g.user.about_me = form.about_me.data
        g.user.email = form.email.data
        g.user.pic_url = form.pic_url.data
        db.session.add(g.user)
        db.session.commit()
        flash(choice(app.config['MSG']['confirm_post']))
        return redirect(url_for('user', handle=g.user.handle, page=1))
    else:
        form.handle.data = g.user.handle
        form.about_me.data = g.user.about_me
        form.email.data = g.user.email
        form.pic_url.data = g.user.pic_url
        if form.handle.errors:
            flash(form.handle.errors[0])
    return render_template('edit_user.html', form=form, user=g.user)

@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    form = EditPostForm()
    post = Post.query.get(id)
    if post is None:
        flash("What? I know no post such as this.")
        return redirect(url_for('index'))
    if post.author.id != g.user.id:
        flash('You cannot edit this post!')
        return redirect(url_for('index'))
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('History revised.')
        return redirect(url_for('index'))
    else:
        form.body.data = post.body
    return render_template('edit_post.html', form=form, post=post)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = Post.query.get(id)
    if post is None:
        flash("What? I know no post such as this.")
        return redirect(url_for('index'))
    if post.author.id != g.user.id:
        flash('You cannot delete this post!')
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash('Probably better off this way.')
    return redirect(url_for('index'))

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
        return redirect(url_for('user', handle=handle, page=1))
    u = g.user.unfollow(user)
    if u is None:
        flash('That\'s weird, you can\'t unfollow ' + handle + '.')
        return redirect(url_for('user', handle=handle, page=1))
    db.session.add(u)
    db.session.commit()
    flash('You have unfollowed ' + handle + '.')
    return redirect(url_for('user', handle=handle, page=1))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', user=g.user), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html', user=g.user), 500

def get_inspiration():
    return choice(app.config['MSG']['inspiration'])