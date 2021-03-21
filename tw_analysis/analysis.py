#!/usr/bin/env python3

import dateutil.parser as parser
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib import colors as mcolors
import numpy as np

from collections import Counter
import pandas as pd
import calendar
from pathlib import Path, PurePath
import os
from scipy.stats import linregress
import tweepy

from tw_analysis import config  # loads twitter credentials and potential

analysis_path = PurePath(Path.home(), config.project_name)
if not (os.path.isdir(analysis_path)):
    os.makedirs(analysis_path)

df_filename = "tweets_df.pkl"
reload_tweets = False


df_file = PurePath(analysis_path, df_filename)

#%%
"""
Gather data
"""
consumer_key = config.twitter_keys["consumer_key"]
consumer_secret = config.twitter_keys["consumer_secret"]
access_token = config.twitter_keys["access_token_key"]
access_token_secret = config.twitter_keys["access_token_secret"]
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

#%%
"""
Load data
"""
if reload_tweets or not (os.path.exists(df_file)):
    earliest_ID = None
    tweets = []

    # fetch data
    while True:  # twitter allows only fetching 3200 tweets
        print(f"Numnber of tweets: {len(tweets)}")
        if earliest_ID:
            timeline_fetch = api.user_timeline(
                screen_name=config.user,
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
    df = pd.DataFrame(tweet_dicts)
    df.to_pickle(PurePath(analysis_path, df_filename))
else:
    df = pd.read_pickle(df_file)


quoted_df = df[df.is_quote_status == True]
replys_df = df[df.in_reply_to_status_id > 0]
except_replys_df = df[np.isnan(df.in_reply_to_status_id)]
assert len(replys_df) + len(except_replys_df) == len(df)
#%%
"""
Analysis
"""


def plot_time_distribution(
    df,
    times,
    color_counter_key: str = "retweets",
    filename: str = None,
    show_plot: bool = False,
):
    grouped = df.groupby([times.hour])
    count = grouped.created_at.count()
    if color_counter_key == "likes":
        color_counter = grouped.favorite_count.mean()
    else:
        color_counter = grouped.retweet_count.mean()
    max_color_counter = color_counter.max()
    min_color_counter = color_counter.min()
    norm = mcolors.Normalize(vmin=min_color_counter, vmax=max_color_counter)
    cmap = cm.get_cmap("cool")
    plt.xlabel("Time of day")
    plt.ylabel("Number of posts")
    bar_colors = [cmap(norm(x)) for x in color_counter]
    plt.bar(count.index, count.values, color=bar_colors)
    sm = cm.ScalarMappable(
        cmap=cmap, norm=plt.Normalize(min_color_counter, max_color_counter)
    )
    cbar = plt.colorbar(sm)
    cbar.set_label(f"Mean of {color_counter_key}")
    if filename:
        plt.savefig(PurePath(analysis_path, filename), bbox_inches="tight")
    if show_plot:
        plt.show()
    else:
        plt.close()


def plot_date_distribution(
    df,
    times,
    color_counter_key: str = "retweets",
    filename: str = None,
    show_plot: bool = False,
):
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
    cmap = cm.get_cmap("cool")
    idx = count.index
    max_year = max([year for month, year in idx])
    max_month = max([month for month, year in idx if year == max_year])
    min_year = min([year for month, year in idx])
    min_month = min([month for month, year in idx if year == min_year])
    recorded_duration_months = (max_year - min_year) * 12 + (max_month - min_month) + 1
    positions = []
    n_posts = []
    labels = []
    for i in idx:
        year = i[1]
        month = i[0]
        positions.append(
            recorded_duration_months - 12 * (max_year - year) - (max_month - month) - 1
        )
        n_posts.append(count[i])
        labels.append(f"{calendar.month_abbr[month]}, {year}")
    bar_colors = [cmap(norm(x)) for x in color_counter]
    plt.bar(positions, n_posts, color=bar_colors)
    sm = cm.ScalarMappable(
        cmap=cmap, norm=plt.Normalize(min_color_counter, max_color_counter)
    )
    cbar = plt.colorbar(sm)
    plt.xticks(positions, labels, rotation=90)
    plt.xlabel("Month of posts")
    plt.ylabel("Number of posts")
    cbar.set_label(f"Mean of {color_counter_key}")
    if filename:
        plt.savefig(PurePath(analysis_path, filename), bbox_inches="tight")
    if show_plot:
        plt.show()
    else:
        plt.close()


def create_colormap():
    cvals = [0, 0.05, 0.0501, 1]
    colors = ["red", "red", "violet", "blue"]
    norm = plt.Normalize(min(cvals), max(cvals))
    tuples = list(zip(map(norm, cvals), colors))
    cmap = mcolors.LinearSegmentedColormap.from_list("", tuples)
    return cmap


def plot_example_colormap():
    x, y, c = zip(*np.random.rand(30, 3) * 4 - 2)
    norm = plt.Normalize(0, 1)
    cmap = create_colormap()
    plt.scatter(x, y, c=c, cmap=cmap, norm=norm)
    plt.colorbar()
    plt.show()


def plot_vs_tweetlength(df, key="likes", filename=None, show_plot: bool = False):
    """
    Plot likes or RTs vs. tweetlength
    """
    from sklearn.linear_model import LinearRegression

    x = [len(text) for text in df.full_text]
    if key == "likes":
        y = np.nan_to_num(np.array(list(df.favorite_count)))
    else:
        y = np.nan_to_num(np.array(list(df.retweet_count)))

    plt.plot(x, y, "o")
    plt.title(f"Number of {key} vs. tweet length")
    plt.xlabel("Characters of tweet")
    plt.ylabel(f"Number of {key}")
    experiment_linear_regression = linregress(x, y)
    pVal = experiment_linear_regression.pvalue
    plt.text(max(x) / 2, max(y) / 2, f"P = {pVal:.4}")
    result_string = f"Correlation of {key} and nuumber of characters: Pearson Coefficient = {experiment_linear_regression.rvalue:.4f}, p-Value=  {pVal:.4f}"
    print(result_string)
    result_string = f"MEP increase: Slope = {experiment_linear_regression.slope:.6f}, Intercept={experiment_linear_regression.intercept:.6f}"
    linear_fit = []
    for i in x:
        y = (
            experiment_linear_regression.slope * i
            + experiment_linear_regression.intercept
        )
        linear_fit.append(y)
    plt.plot(x, linear_fit)
    if filename:
        plt.savefig(PurePath(analysis_path, filename), bbox_inches="tight")
    if not (show_plot):
        plt.close()


#%%
times = pd.DatetimeIndex(except_replys_df.created_at)
plot_time_distribution(
    except_replys_df,
    times,
    filename="times_retweets",
    color_counter_key="retweets",
    show_plot=True,
)
plot_time_distribution(
    except_replys_df,
    times,
    filename="times_likes",
    color_counter_key="likes",
    show_plot=True,
)
plot_date_distribution(
    except_replys_df,
    times,
    filename="date_likes",
    color_counter_key="likes",
    show_plot=True,
)
plot_vs_tweetlength(
    except_replys_df, filename="tweetlength_vs_likes", key="likes", show_plot=True
)
plot_vs_tweetlength(
    except_replys_df, filename="tweetlength_vs_rts", key="retweets", show_plot=True
)
#%%


print(f"{len(tweets)} tweets cached")

percent_quoted = 100 * len(quoted_df) / len(df)
percent_replies = 100 * len(replys_df) / len(df)
print(f"{percent_quoted}% where quoted tweets")
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
    if DEBUG:
        print(f"\nText: {tweet.full_text}")
    try:
        tweet.entities["media"]
        if DEBUG:
            print("Tweeted with media")
        media_rts.append(tweet.retweet_count)
        media_favs.append(tweet.favorite_count)
    except KeyError:
        no_media_rts.append(tweet.retweet_count)
        no_media_favs.append(tweet.favorite_count)
    if DEBUG:
        print(f"RT: {tweet.retweet_count}, Favs: {tweet.favorite_count}")
    datetimes.append(tweet.created_at)


#%%
dt_start = datetimes[-1]
dt_end = datetimes[0]
print(f"Starting analysis at {tweets[-1].created_at}")
print(f"Ending analysis at {tweets[0].created_at}")


delta = dt_end - dt_start
print(
    f"So the analysis covers {delta.days} days. There have been {len(tweets)/delta.days:.3} tweets/per day."
)

weekdays = []
hours = []
for tweetdate in datetimes:
    weekdays.append(tweetdate.strftime("%A"))
    hours.append(tweetdate.time())


counted_weekdays = dict(Counter(weekdays))

tweets_per_weekday = counted_weekdays
for weekday in tweets_per_weekday:
    tweets_per_weekday[weekday] = tweets_per_weekday[weekday] / (delta.days / 7)
plt.plot(list(tweets_per_weekday.keys())[::-1], list(tweets_per_weekday.values())[::-1])

#%%


print(f"Mean RTs: {np.mean(rts):.4}")
print(f"Mean RTs with media: {np.mean(media_rts):.4}")
print(f"Mean RTs without media: {np.mean(no_media_rts):.4}")


print(f"Mean favs: {np.mean(favs):.4}")
print(f"Mean favs with media: {np.mean(media_favs):.4}")
print(f"Mean favs without media: {np.mean(no_media_favs):.4}")
