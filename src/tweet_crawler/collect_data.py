import os
import tweepy
import pandas as pd

def get_tweets_and_save(bearer_token: str, company_tweet: str) -> None:
    # ========================
    # 1. Authenticate
    # ========================
    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)

    # ========================
    # 2. Get User ID for @TLRailUK
    # ========================
    user = client.get_user(username=company_tweet)
    user_id = user.data.id
    print(f"TLRailUK user ID: {user_id}")

    # ===============================
    # 3. Retrieve Latest 100 Tweets
    # ===============================
    tweets_data = []

    for response in tweepy.Paginator(
        client.get_users_tweets,
        id=user_id,
        tweet_fields=["created_at", "public_metrics", "text"],
        max_results=100  # max per request
    ).flatten(limit=100):  # limit total number
        tweets_data.append({
            "created_at": response.created_at,
            "text": response.text,
            "retweets": response.public_metrics.get("retweet_count", 0),
            "likes": response.public_metrics.get("like_count", 0),
            "replies": response.public_metrics.get("reply_count", 0),
            "quotes": response.public_metrics.get("quote_count", 0)
        })

    # ===============================
    # 4. Save to CSV
    # ===============================
    df = pd.DataFrame(tweets_data)
    df.to_csv("./TLRailUK_latest_100_tweets.csv", index=False)

    print(f"✅ Retrieved {len(df)} tweets and saved to TLRailUK_latest_100_tweets.csv")


def get_tweets_from_users_and_save(bearer_token: str, company_tweet: str) -> None:
    # ========================
    # 1. Authenticate
    # ========================
    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)

    # ========================
    # 2. Get User ID for @TLRailUK
    # ========================
    user = client.get_user(username=company_tweet)
    user_id = user.data.id
    print(f"TLRailUK user ID: {user_id}")

    # ========================
    # 3. Get Followers
    # ========================
    followers = []
    for response in tweepy.Paginator(client.get_users_followers, id=user_id, max_results=1000):
        if response.data:
            followers.extend(response.data)
        else:
            break

    print(f"Collected {len(followers)} followers")

    # ========================
    # 4. Get Recent Tweets from Followers
    # ========================
    tweets_data = []

    for follower in followers:  # Limit for demonstration
        try:
            tweets = client.get_users_tweets(
                id=follower.id,
                max_results=10,  # Most recent 10 tweets per follower
                tweet_fields=["created_at", "public_metrics", "text"]
            )
            if tweets.data:
                for tweet in tweets.data:
                    tweets_data.append({
                        "follower_username": follower.username,
                        "tweet_text": tweet.text,
                        "created_at": tweet.created_at,
                        "retweets": tweet.public_metrics['retweet_count'],
                        "likes": tweet.public_metrics['like_count']
                    })
        except Exception as e:
            print(f"Skipping {follower.username} due to error: {e}")

    # ========================
    # 5. Save to CSV
    # ========================
    df = pd.DataFrame(tweets_data)
    df.to_csv("./tlrailuk_follower_tweets.csv", index=False)
    print("Saved tweets to ./tlrailuk_follower_tweets.csv")
    