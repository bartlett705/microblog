from flask import render_template, flash, redirect
from app import app
from .forms import LoginForm

@app.route('/')
@app.route('/index')
def index():
        user = {'nickname': 'Fanny'} # Placeholder
        posts = [  # fake array of posts
        {
            'author': {'nickname': 'Sir Elderberry'},
            'body': 'Your mother was a hamster!'
        },
        {
            'author': {'nickname': 'The Bunny'},
            'body': 'Fear my pointy teefs!'
        }
    ]
	return render_template('index.html', title='Home', user=user, posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
    	flash('ID="%s", remember_me=%s' % (form.openid.data, str(form.remember_me.data)))
    	return redirect('/index')
    return render_template('login.html',
                           title='Validate Credentials',
                           form=form, providers=app.config['OPENID_PROVIDERS'])
