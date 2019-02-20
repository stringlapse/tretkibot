import praw

def login():
    reddit = praw.Reddit(client_id='XXXXX',
                     client_secret='XXXXX',
                     password='XXXXX',
                     user_agent='XXXXX',
                     username='XXXXX')
    return reddit


login