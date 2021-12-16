'''Handles connection to Twitter API using Tweepy'''

from os import getenv
import tweepy
import spacy
from .models import DB, Tweet, User

# Get API Key from environment vars.
key = getenv('TWITTER_API_KEY')
secret = getenv('TWITTER_API_KEY_SECRET')

# Connect to the Twitter API
TWITTER_AUTH = tweepy.OAuthHandler(key, secret)
TWITTER = tweepy.API(TWITTER_AUTH)

def add_or_update_user(username):
    """
    Gets twitter user and tweets from twitter DB
    Gets user by "username" parameter.
    """
    try:
        # gets back twitter user object
        twitter_user = TWITTER.get_user(username)
        # Either updates or adds user to our DB
        db_user = (User.query.get(twitter_user.id)) or User(
            id=twitter_user.id, name=username)
        DB.session.add(db_user)  # Add user if don't exist

        # Grabbing tweets from "twitter_user"
        tweets = twitter_user.timeline(
            count=200,
            exclude_replies=True,
            include_rts=False,
            tweet_mode="extended",
            since_id=db_user.newest_tweet_id
        )

        # check to see if the newest tweet in the DB is equal to the newest tweet from the Twitter API, if they're not equal then that means that the user has posted new tweets that we should add to our DB. 
        if tweets:
            db_user.newest_tweet_id = tweets[0].id

        # tweets is a list of tweet objects
        for tweet in tweets:
            # type(tweet) == object
            # Turn each tweet into a word embedding. (vectorization)
            tweet_vector = vectorize_tweets(tweet.text)
            db_tweet = Tweet(
                id=tweet.id,
                text=tweet.text,
                vect=tweet_vector
            )
            db_user.tweets.append(db_tweet)
            DB.session.add(db_tweet)

    except Exception as e:
        print("Error processing {}: {}".format(username, e))
        raise e

    else:
        DB.session.commit()

def update_all_users():
    usernames = []
    Users = User.query.all()
    for user in Users:
        usernames.apppend(user.username)
    
    return usernames

# Load our pretrained SpaCy Word Embeddings model
nlp = spacy.load('my_model/')

# Turn tweet text into word embeddings.
def vectorize_tweets(tweet_text):
    return nlp(tweet_text).vector