from time import time
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired

class Tweeter:
    def __init__(self, username, id, last_checked, followers):
        self.username = username
        self.id = id
        self.last_checked = last_checked
        self.followers = followers.split(",")
    
    def from_row(row):
        tweeter = Tweeter(row[0], row[1], row[2], row[3])
        return tweeter

# CREATE TABLE tweets (id text unique, text text, author text, timestamp text, image_url text, likes int, rts int, sent integer);
class Tweet:
    def __init__(self, id, text, author, timestamp, image_url, likes, rts, sent):
        self.id = id
        self.text = text
        self.author = author
        self.timestamp = timestamp
        self.image_url = image_url
        self.likes = likes
        self.rts = rts
        self.sent = sent
    
    def fromRow(row):
        if len(row) != 8:
            raise DatabaseObjectConversionException("Tweet object needs 8 attributes to properly convert.")
        return Tweet(
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7]
        )

class User:
    def __init__(self, email):
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        self.email = email

    def login(self, email):
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        self.email = email
    
    def logout(self):
        self.is_authenticated = False
        self.is_active = False
        self.is_anonymous = True
        self.email = None
    
    def get_id(self):
        return self.email


class NewFollowForm(FlaskForm):
    new_user = StringField("Enter new username")
    submit = SubmitField("Follow")
# class FollowersForm(FlaskForm):
#     following = SelectMultipleField("Following")

#     def setFollowing(self, choices):
#         self.following = SelectMultipleField("Following", choices=choices)

class LoginForm(FlaskForm):
    username = StringField('email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
        
class RegisterForm(FlaskForm):
    username = StringField('email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign up')

class SendPreviousForm(FlaskForm):
    submit = SubmitField("Send me this week's digest")

class SendOnDemandForm(FlaskForm):
    submit = SubmitField("Send me this week's digest")


class DatabaseObjectConversionException(Exception):
    """Custom exception when converting db objects"""