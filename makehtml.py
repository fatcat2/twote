from typing import List
from dbhelper import get_connection
from models import Tweet, Tweeter

header = """<html>
    <style>
        body {
            display: flex;
            justify-content: center;
        }
        .container {
            width: 100%;
        }
        @media only screen and (min-width: 500px) {
            .container {
                width: 70%;
            }
        }
    </style>
    <body>
        <div class="container">
            <p>Hi! Here are the tweets you missed.</p>
            <hr/>"""

footer = """        </div>
    </body>
</html>"""

def generateTweetLink(tweet: Tweet):
    return f"https://twitter.com/{tweet.author}/status/{tweet.id}"

def generateTweet(tweet: Tweet):
    return f"<p><b>@{tweet.author}</b> — {tweet.text} </p>" + \
           f" <p>{tweet.likes} likes, {tweet.rts} RTs | <a href=\"{generateTweetLink(tweet)}\"/>{tweet.timestamp}</a></p>" + \
            "<hr/>"


def createEmail(tweets: List[Tweet]):
    # with open("email-test.html", "w+") as file:
    #     file.write(header)
    #     print(tweets)
    #     for tweet in tweets:
    #         file.write(generateTweet(tweet))
    #     file.write(footer)
    return header + "".join([generateTweet(tweet) for tweet in tweets]) + footer
    
