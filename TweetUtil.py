import sqlite3
from pytwitter import Api

def updateTweetTable(api: Api):
    conn = sqlite3.connect("data.sqlite")
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
    conn.close()