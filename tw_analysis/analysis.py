#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dateutil.parser as parser
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib import colors as mcolors
import numpy as np

from collections import Counter
import twitter
import pandas as pd
import calendar
from pathlib import Path, PurePath
import os


from tw_analysis import config # loads twitter credentials and potential 

analysis_path = PurePath(Path.home(), config.project_name)
if not(os.path.isdir(analysis_path)):
    os.makedirs(analysis_path)

df_filename = "tweets_df.pkl"

filepath = "tmp.pkl"
#%%
"""
Gather data
"""
api = twitter.Api(consumer_key=config.twitter_keys['consumer_key'],
                  consumer_secret=config.twitter_keys['consumer_secret'],
                  access_token_key=config.twitter_keys['access_token_key'],
                  access_token_secret=config.twitter_keys['access_token_secret'])
#%%


tweets = []
earliest_ID = None
#%%
for i in range (0,80):
    tweets.extend(api.GetUserTimeline(screen_name=config.user,
                                      count = 200,
                                      include_rts=False,
                                      exclude_replies=True,
                                      max_id = earliest_ID))
    earliest_ID = tweets[-1].id

#%%
# Create and store a dataframe
tweet_dicts = []
for tweet in tweets:
    tweet_as_dict = tweet.AsDict()
    tweet_dicts.append(tweet_as_dict)

df = pd.DataFrame(tweet_dicts)


df.to_pickle(PurePath(analysis_path, df_filename))


#%%
"""
Load data
"""
df = pd.read_pickle(PurePath(analysis_path, df_filename))


#%%
"""
Analysis
"""

def plot_time_distribution(df,
                           times,
                           color_counter_key:str = "retweets",
                           filename:str = None):
    grouped = df.groupby([times.hour])
    count = grouped.created_at.count()
    if color_counter_key == "likes":
        color_counter = grouped.favorite_count.mean()
    else:
        color_counter = grouped.retweet_count.mean()
    max_color_counter = color_counter.max()
    min_color_counter = color_counter.min()
    norm = mcolors.Normalize(vmin=min_color_counter, vmax=max_color_counter)
    cmap = cm.get_cmap('cool')
    plt.xlabel("Time of day")
    plt.ylabel("Number of posts")
    bar_colors = [cmap(norm(x)) for x in color_counter]
    plt.bar(count.index, count.values, color = bar_colors)
    sm = cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(min_color_counter, max_color_counter))
    cbar = plt.colorbar(sm)
    cbar.set_label(f"Mean of {color_counter_key}")
    if filename:
        plt.savefig(PurePath(analysis_path, filename), bbox_inches = "tight")

def plot_date_distribution(df,
                           times,
                           color_counter_key:str = "retweets",
                           filename:str = None):
    """ Plots the number of actions per month starting with begin of data"""
    grouped = df.groupby([times.month, times.year])
    count = grouped.created_at.count()
    if color_counter_key == "likes":
        color_counter = grouped.favorite_count.mean()
    else:
        color_counter = grouped.retweet_count.mean()
    max_color_counter = color_counter.max()
    min_color_counter = color_counter.min()
    norm = mcolors.Normalize(vmin=min_color_counter, vmax=max_color_counter)
    cmap = cm.get_cmap('cool')
    idx = count.index
    max_year = max([year for month, year in idx])
    max_month = max([month for month, year in idx if year == max_year])
    min_year = min([year for month, year in idx])
    min_month = min([month for month, year in idx if year == min_year])
    recorded_duration_months = (max_year-min_year)*12+(max_month-min_month)+1
    positions = []
    n_posts = []
    labels = []
    for i in idx:
        year = i[1]
        month = i[0]
        positions.append(recorded_duration_months-12*(max_year-year)-(max_month-month)-1)
        n_posts.append(count[i])
        labels.append(f"{calendar.month_abbr[month]}, {year}")
    bar_colors = [cmap(norm(x)) for x in color_counter]
    plt.bar(positions, n_posts, color = bar_colors)
    sm = cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(min_color_counter, max_color_counter))
    cbar = plt.colorbar(sm)
    plt.xticks(positions, labels, rotation=90)
    plt.xlabel("Month of posts")
    plt.ylabel("Number of posts")
    cbar.set_label(f"Mean of {color_counter_key}")
    plt.show()
    if filename:
        plt.savefig(PurePath(analysis_path, filename), bbox_inches = "tight")

def create_colormap():
    cvals  = [0, 0.05, 0.0501, 1]
    colors = ["red","red","violet","blue"]
    norm=plt.Normalize(min(cvals),max(cvals))
    tuples = list(zip(map(norm,cvals), colors))
    cmap = mcolors.LinearSegmentedColormap.from_list("", tuples)
    return cmap

def plot_example_colormap():
    x,y,c = zip(*np.random.rand(30,3)*4-2)
    norm=plt.Normalize(0,1)
    cmap = create_colormap()
    plt.scatter(x,y,c=c, cmap=cmap, norm=norm)
    plt.colorbar()
    plt.show()


#%%
times = pd.DatetimeIndex(df.created_at)
plot_time_distribution(df, times, filename="times_retweets", color_counter_key = "retweets")
plot_time_distribution(df, times, filename="times_likes", color_counter_key = "likes")
plot_date_distribution(df, times, filename="date_likes", color_counter_key = "likes")
#%%


print(f"{len(tweets)} tweets cached")

rts = []
media_rts = []
no_media_rts = []
favs = []
media_favs = []
no_media_favs = []
datetimes = []
for tweet in tweets:
    rts.append(tweet.retweet_count)
    favs.append(tweet.favorite_count)
    print(f"\nText: {tweet.text}")
    if tweet.media:
        print("Tweeted with media")
        media_rts.append(tweet.retweet_count)
        media_favs.append(tweet.favorite_count)
    else:
        no_media_rts.append(tweet.retweet_count)
        no_media_favs.append(tweet.favorite_count)
    print(f"RT: {tweet.retweet_count}, Favs: {tweet.favorite_count}")
    if tweet.withheld_in_countries:
        print (f"Withheld in {tweet.withheld_in_countries}")

    #weekdays.append(tweet.created_at[:3])
    #dt = datetime.strptime(created_at[-20:], ' %H:%M:%S %z %Y')
    dt = parser.parse(tweet.created_at)
    datetimes.append(dt)


#%%
dt_start = datetimes[-1]
dt_end = datetimes[0]
print(f"Starting analysis at {tweets[-1].created_at}")
print(f"Ending analysis at {tweets[0].created_at}")


delta = dt_end - dt_start
print(f"So the analysis covers {delta.days} days. There have been {len(tweets)/delta.days:.3} tweets/per day.")

weekdays = []
hours = []
for tweetdate in datetimes:
    weekdays.append(tweetdate.strftime('%A'))
    hours.append(tweetdate.time())


counted_weekdays = dict(Counter(weekdays))

tweets_per_weekday = counted_weekdays
for weekday in tweets_per_weekday:
    tweets_per_weekday[weekday] = tweets_per_weekday[weekday]/(delta.days/7)
plt.plot(list(tweets_per_weekday.keys())[::-1], list(tweets_per_weekday.values())[::-1])

#%%


print(f"Mean RTs: {np.mean(rts):.3}")
print(f"Mean RTs with media: {np.mean(media_rts):.3}")
print(f"Mean RTs without media: {np.mean(no_media_rts):.3}")


print(f"Mean favs: {np.mean(favs):.4}")
print(f"Mean favs with media: {np.mean(media_favs):.4}")
print(f"Mean favs without media: {np.mean(no_media_favs):.4}")
