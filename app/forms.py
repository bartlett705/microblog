from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length
from app.models import User

class EditForm(Form):
    handle = StringField('handle', validators=[DataRequired()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=240)])

    def __init__(self, original_handle, *args, **kwargs):
    	Form.__init__(self, *args, **kwargs)
    	self.original_handle = original_handle

	def validate(self):
		if not Form.validate(self):
			return False
		if self.handle.data == self.original_handle:
			return True
		user = User.query.filter_by(handle=self.handle.data).first()
        if user != None:
            self.handle.errors.append('Somebody already has that handle; choose another.')
            return False
        return True

class PostForm(Form):
    post = StringField('post', validators=[DataRequired()])