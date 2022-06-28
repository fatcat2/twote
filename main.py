import os
import bcrypt
from datetime import datetime
from time import time
import base64

from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect

from pytwitter import Api
from TweetUtil import updateTweetTable

from dbhelper import get_connection
from makehtml import createEmail
from models import *
from EmailUtil import sendEmail

app = Flask(__name__)
app.config["SECRET_KEY"] = "test"
api = Api(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))
login_manager = LoginManager()
login_manager.init_app(app)
csrf = CSRFProtect(app)
cache = Cache(app)

@app.route("/", methods=["GET", "POST"])
def index():
    new_user_form = NewFollowForm()
    if current_user.is_authenticated:
        if new_user_form.validate_on_submit():
            new_user = new_user_form.new_user.data
            last_checked = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f%z')

            new_user_response = api.get_user(username=new_user).data

            conn = get_connection()
            c = conn.cursor()
            c.execute("insert into following values(?,?,?,?)", (new_user, new_user_response.id, last_checked, current_user.get_id()))
            conn.commit()
            conn.close()

        follow = [(user.username,user.username) for user in get_following(current_user.get_id())]
        class FollowersForm(FlaskForm):
            following = SelectMultipleField("Following", choices=follow)
            submit = SubmitField("Remove user")

        form = FollowersForm()

        return render_template("home.html", form=form, new_user_form=new_user_form, sendform=SendPreviousForm())

    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        conn = get_connection()
        c = conn.cursor()
        c.execute("select hash from users where email=?", (form.username.data,))
        results = c.fetchall()
        conn.close()

        if len(results) != 1:
            flash("Could not authenticate")
        else:
            decoded_hash = results[0][0]
            hash = decoded_hash.encode("UTF-8")

            password = form.password.data.encode("utf-8")

            if bcrypt.checkpw(password=password, hashed_password=hash):
                user = User(form.username.data)
                login_user(user=user)
                return redirect(url_for("index"))
            else:
                flash("Could not authenticate")

    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.username.data
        password = form.password
        bytes = password.data.encode("utf-8")
        salt = bcrypt.gensalt()
        hash = bcrypt.hashpw(bytes, salt)

        decoded_hash = hash.decode()

        conn = get_connection()
        c = conn.cursor()
        c.execute("insert into users values(?,?)", (email, decoded_hash,))
        conn.commit()
        conn.close()

        login_user(User(email))

        return redirect(url_for("index"))
    else:
        print(form.errors)
        print("registration failed")
    return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/auth")
def authback():
    print(request.args)

@app.route("/add_user", methods=["POST"])
@login_required
def add_user():
    username = request.form.get("new_user")
    user = api.get_user(username=username).data

    my_date = datetime.today()
    start_time = my_date.strftime('%Y-%m-%dT%H:%M:%S.%f%z')

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT followers FROM following WHERE username=?", (username,))
    results = c.fetchall()

    if len(results) != 1:
        c.execute("INSERT INTO following values (?,?,?,?)", (username, user.id, start_time, current_user.get_id()))
        conn.commit()
    else:
        followers = results[0][0].strip().split(",")
        followers.append(current_user.get_id())

        new_followers = ",".join(followers)

        c.execute("UPDATE following SET followers=? WHERE username=?", (new_followers, username,))
        conn.commit()

    conn.close()

    return redirect(url_for("index"))


@app.route("/remove_user", methods=["POST"])
@login_required
def remove_user():
    username = request.form.get("following")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM following WHERE username=?", (username,))
    result = c.fetchall()

    if len(result) == 1:
        following_users = result[0][3].split(",")
        new_following_users = ",".join([user for user in following_users if user != current_user.get_id()])
        c.execute("UPDATE following SET followers=? WHERE username=?", (new_following_users, username))
        c.execute("SELECT * FROM following WHERE username=?", (username,))
        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.route("/sendprevious", methods=["POST"])
@login_required
def send_prev():
    conn = get_connection()
    c = conn.cursor()
    c.execute("select * from digests where email=? order by timestamp desc limit 1;", (current_user.get_id(),))
    previous_digest = c.fetchone()[1]
    conn.close()

    html = base64.b64decode(previous_digest.encode("utf-8")).decode()

    sendEmail(current_user.get_id(), html)

    flash("✅ weekly digest sent!")

    return redirect(url_for("index"))


@app.route("/sendbatch", methods=["GET"])
def send_batch():
    updateTweetTable(api)

    conn = get_connection()
    c = conn.cursor()
    c.execute("select email from users")

    emails = [row[0] for row in c.fetchall()]
    c.execute("select tweets.id, tweets.text, following.username, tweets.timestamp, tweets.image_url, tweets.likes, tweets.rts, tweets.sent text from tweets join following on following.id=tweets.author where tweets.sent=False")
    tweets_results = c.fetchall()

    for email in emails:
        current_user_following = [user.username for user in get_following(email)]

        tweets = [Tweet.fromRow(row) for row in tweets_results if row[2] in current_user_following]
        html = createEmail(tweets);
        sendEmail(email, html)

        encoded = base64.b64encode(html.encode("utf-8")).decode()
        curr_time = int(datetime.now().timestamp())

        c.execute("insert into digests values (?,?,?)", (current_user.get_id(), encoded, curr_time))
        conn.commit()

    conn.close()

    flash("✅ weekly digest sent!")

    return redirect(url_for("index"))


@app.route("/get")
def get_tweets():
    conn = get_connection()
    c = conn.cursor()
    c.execute("select * from following")
    users = c.fetchall()
    
    for user in users:
        timeline = api.get_timelines(
            user_id=user[1], 
            tweet_fields=["created_at", "public_metrics"], 
            media_fields=["url"],
            expansions=["attachments.media_keys"]   
        )
        if timeline.includes is not None:
            images = {media.media_key: media.url for media in timeline.includes.media}

        tweets = [
                (item.id, item.text, user[1], item.created_at, item.attachments, item.public_metrics.like_count, item.public_metrics.retweet_count, False,) 
                for item in timeline.data
        ]

        for tweet in tweets:
            print(tweet)
            tweet = list(tweet)
            text_list = tweet[1].split()
            print(text_list)
            if len(tweet[1]) > 2 and text_list[0] == "RT":
                tweet[5] = 0
                tweet[6] = 0
                continue
            
            if tweet[4] is not None:
                tweet[4] = images.get(tweet[4].media_keys[0])

            try:
                c.execute("insert into tweets values(?,?,?,?,?,?,?,?)", tuple(tweet))
            except:
                pass
    
    conn.commit()

    return {"twts":""}


@cache.memoize(10)
def get_following(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("select * from following")
    results = c.fetchall()
    conn.close()

    users = [user for user in [Tweeter.from_row(row) for row in results] if username in user.followers]

    return users


@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("select * from users where email=?", (user_id,))
    email = c.fetchall()
    conn.close()

    if len(email) == 1:
        return User(email[0][0])
    else:
        None


if __name__=="__main__":
    app.run(host="0.0.0.0", port=5100)
