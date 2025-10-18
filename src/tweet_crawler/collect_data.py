import os
import tweepy
import time
import pandas as pd

def como():
    print('asa')
    
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
    

def craw_with_replies(bearer_token: str, company_tweet: str, with_research=False) -> None:
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
    # 3. Get 100 Latest Tweets
    # ===============================
    tweets = []
    for response in tweepy.Paginator(
        client.get_users_tweets,
        id=user_id,
        tweet_fields=["created_at", "public_metrics", "conversation_id", "text"],
        exclude=None,  # include retweets/replies if desired
        max_results=100
    ).flatten(limit=100):
        tweets.append(response)

    print(f"Collected {len(tweets)} tweets from @TLRailUK")

    if not with_research:
        # ===============================
        # 4. Get Replies for Each Tweet
        # ===============================
        replies_data = []

        for tweet in tweets:
            query = f"conversation_id:{tweet.conversation_id} -from:TLRailUK"
            try:
                search_results = client.search_recent_tweets(
                    query=query,
                    tweet_fields=["created_at", "author_id", "text", "public_metrics"],
                    max_results=50  # limit per tweet to avoid rate limits
                )
                if search_results.data:
                    for reply in search_results.data:
                        replies_data.append({
                            "original_tweet_id": tweet.id,
                            "original_tweet_text": tweet.text,
                            "reply_text": reply.text,
                            "reply_author_id": reply.author_id,
                            "reply_created_at": reply.created_at,
                            "reply_likes": reply.public_metrics.get("like_count", 0),
                        })
                time.sleep(1)  # be polite to API
            except Exception as e:
                print(f"Error getting replies for tweet {tweet.id}: {e}")

        # ===============================
        # 5. Save Results
        # ===============================
        df = pd.DataFrame(replies_data)
        df.to_csv("TLRailUK_tweets_with_replies.csv", index=False)

        print(f"✅ Collected replies for {len(tweets)} tweets and saved to TLRailUK_tweets_with_replies.csv")

    else:
        # ===============================
        # 4. Get All Historical Replies
        # ===============================
        replies_data = []

        for i, tweet in enumerate(tweets, start=1):
            query = f"conversation_id:{tweet.id} -from:TLRailUK"
            print(f"[{i}/{len(tweets)}] Fetching replies for tweet ID {tweet.id}...")

            try:
                for page in tweepy.Paginator(
                    client.search_all_tweets,
                    query=query,
                    tweet_fields=["created_at", "author_id", "text", "public_metrics", "in_reply_to_user_id"],
                    expansions=["author_id"],
                    max_results=100
                ):
                    if page.data:
                        for reply in page.data:
                            replies_data.append({
                                "original_tweet_id": tweet.id,
                                "original_tweet_text": tweet.text,
                                "reply_text": reply.text,
                                "reply_author_id": reply.author_id,
                                "reply_created_at": reply.created_at,
                                "reply_likes": reply.public_metrics.get("like_count", 0)
                            })
                time.sleep(1)  # polite delay between tweets
            except Exception as e:
                print(f"Error fetching replies for tweet {tweet.id}: {e}")

        # ===============================
        # 5. Save to CSV
        # ===============================
        df = pd.DataFrame(replies_data)
        df.to_csv("TLRailUK_tweets_with_all_replies.csv", index=False)

        print(f"✅ Collected replies for {len(tweets)} tweets and saved to TLRailUK_tweets_with_all_replies.csv")

def crawl_with_dates(bearer_token: str, company_tweet: str, with_research=True) -> None:
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
    # 3. Define Date Range for April 2025
    # ===============================
    start_time = "2025-04-01T00:00:00Z"
    end_time   = "2025-05-01T00:00:00Z"

    # ===============================
    # 4. Search Tweets from April 2025
    # ===============================
    query = f"from:TLRailUK -is:retweet"

    tweets_data = []

    for response in tweepy.Paginator(
        client.search_all_tweets,  # use search_recent_tweets if you don't have Academic Research access
        query=query,
        tweet_fields=["created_at", "public_metrics", "text"],
        start_time=start_time,
        end_time=end_time,
        max_results=100
    ).flatten(limit=100):
        tweets_data.append({
            "created_at": response.created_at,
            "text": response.text,
            "retweets": response.public_metrics.get("retweet_count", 0),
            "likes": response.public_metrics.get("like_count", 0),
            "replies": response.public_metrics.get("reply_count", 0),
            "quotes": response.public_metrics.get("quote_count", 0),
        })

    # ===============================
    # 5. Save to CSV
    # ===============================
    df = pd.DataFrame(tweets_data)
    df.to_csv("TLRailUK_April2025_tweets.csv", index=False)

    print(f"✅ Retrieved {len(df)} tweets from @TLRailUK in April 2025 and saved to TLRailUK_April2025_tweets.csv")
