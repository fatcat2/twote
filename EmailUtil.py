import os
import requests

def sendEmail(username: str, email: str):
    r = requests.post(
        os.getenv("MAILGUN_DOMAIN"),
        auth=("api", os.getenv("MAILGUN_KEY")),
        data={
            "from": "tweetcap@torrtle.co",
            "to": username,
            "subject": "tweets you missed!",
            "html": email
        }
    )

    r.raise_for_status()

    return r

