#!/usr/bin/env python3


import pandas as pd
from pathlib import Path, PurePath
import os
import tweepy

from tw_analysis import config  # loads twitter credentials and target

analysis_path = PurePath(Path.home(), config.project_name)
if not (os.path.isdir(analysis_path)):
    os.makedirs(analysis_path)


df_filename = "tweets_df.pkl"
reload_tweets = False


df_file = PurePath(analysis_path, config.df_filename)

#%%
def prepare_api():
    """
    Prepares the api with the details given in the config-file

    Returns
    -------
    api : api object
        Returns a valid API object.

    """
    consumer_key = config.twitter_keys["consumer_key"]
    consumer_secret = config.twitter_keys["consumer_secret"]
    access_token = config.twitter_keys["access_token_key"]
    access_token_secret = config.twitter_keys["access_token_secret"]
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    return api

#%%
"""
Load data
"""

def fetch_tweets_from_twitter(username, api):
    """
    Loads tweets crom twitter

    Parameters
    ----------
    username: str
        username of the target account.
    api : api object
        Twitter api object.

    Returns
    -------
    tweets: list of tweepy tweet objects
    tweet_dicts : list of dicts
        List of all tweets as dict.

    """
    earliest_ID = None
    tweets = []

    # fetch data
    while True:  # twitter allows only fetching 3200 tweets
        print(f"Numnber of tweets: {len(tweets)}")
        if earliest_ID:
            timeline_fetch = api.user_timeline(
                screen_name=username,
                count=100,
                tweet_mode="extended",
                max_id=earliest_ID - 1,
            )
        else:
            timeline_fetch = api.user_timeline(
                screen_name=config.user, count=100, tweet_mode="extended"
            )
        if len(timeline_fetch) == 0:
            break
        tweets.extend(timeline_fetch)
        earliest_ID = tweets[-1].id
    # Create and store a dataframe
    tweet_dicts = []
    for tweet in tweets:
        tweet_as_dict = tweet.__dict__
        tweet_dicts.append(tweet_as_dict)
    return tweets, tweet_dicts

def load_tweets_of_account(username:str, df_file, reload:bool=False):
    """
    Loads the tweets of an account, stores them in a file

    Parameters
    ----------
    username : str
        username of the target account.
    df_file : Path
        Path to the df.
    reload: bool = False
        If true the tweets will be loaded from twitter, else it will be tried
        to load cached tweets from df_file
    

    Returns
    -------
    df : pandas.DataFrame
        Datafram containing all loadable tweets of the given account.

    """
    if reload or not (os.path.exists(df_file)):
        if config.DEBUG:
            print("Loading tweets from Twitter")
        api = prepare_api()
        tweet_dicts = fetch_tweets_from_twitter(username, api)
        df = pd.DataFrame(tweet_dicts)
        df.to_pickle(PurePath(analysis_path, df_filename))
    else:
        if config.DEBUG:
            print("Loading cached tweets from file")
        df = pd.read_pickle(df_file)
    
    return df
