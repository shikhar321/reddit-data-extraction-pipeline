# =====================================================
# Reddit Scraping + Cleaning Pipeline
# =====================================================

import os
import json
import logging
import praw
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import List, Dict

# =====================================================
# LOAD ENV & CONFIG
# =====================================================
load_dotenv()

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# =====================================================
# LOGGING
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# =====================================================
# REDDIT INSTANCE
# =====================================================
def get_reddit():
    """
    Create authenticated Reddit instance using .env credentials
    """
    client_id = os.getenv("client_id")
    client_secret = os.getenv("client_secret")
    user_agent = os.getenv("user_agent")

    if not all([client_id, client_secret, user_agent]):
        raise ValueError(
            "Missing Reddit API credentials. "
            "Check your .env file."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

# =====================================================
# SCRAPING
# =====================================================
def fetch_comments(submission) -> List[Dict]:
    """
    Recursively fetch all comments and replies for a submission
    """
    submission.comments.replace_more(limit=None)
    data = []

    def walk(comment, parent_id=None):
        data.append({
            "comment_id": comment.id,
            "post_id": submission.id,
            "parent_id": parent_id,
            "body": comment.body,
            "created_utc": comment.created_utc
        })
        for reply in comment.replies:
            walk(reply, comment.id)

    for top_comment in submission.comments:
        walk(top_comment)

    return data


def fetch_data(reddit):
    """
    Fetch top subreddit posts within date range + all comments
    """
    rconf = CONFIG["reddit"]
    subreddit = reddit.subreddit(rconf["subreddit_name"])

    start = datetime.strptime(rconf["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(rconf["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)

    posts = []
    comments = []

    logging.info("Fetching posts from Reddit...")

    for submission in subreddit.top(time_filter="all", limit=None):
        created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)

        if not (start <= created <= end):
            continue

        posts.append({
            "post_id": submission.id,
            "self_text": submission.selftext,
            "created_utc": submission.created_utc,
            "score": submission.score
        })

    if not posts:
        return pd.DataFrame(), pd.DataFrame()

    # Select top N posts by score
    posts = sorted(posts, key=lambda x: x["score"], reverse=True)[:rconf["top_post_number"]]

    logging.info(f"Selected {len(posts)} posts. Fetching comments...")

    for post in posts:
        submission = reddit.submission(id=post["post_id"])
        comments.extend(fetch_comments(submission))

    return pd.DataFrame(posts), pd.DataFrame(comments)

# =====================================================
# CLEANING
# =====================================================
def clean_data(posts_df: pd.DataFrame, comments_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge posts and comments into a single cleaned dataframe
    """
    if posts_df.empty:
        raise ValueError("No posts available to clean.")

    subreddit_name = CONFIG["reddit"]["subreddit_name"]

    # Ensure string consistency
    posts_df["post_id"] = posts_df["post_id"].astype(str)

    if not comments_df.empty:
        comments_df["post_id"] = comments_df["post_id"].astype(str)
        comments_df["comment_id"] = comments_df["comment_id"].astype(str)
        comments_df["parent_id"] = comments_df["parent_id"].astype(str)

    post_ids = set(posts_df["post_id"])
    comment_ids = set(comments_df["comment_id"]) if not comments_df.empty else set()

    def classify(row):
        if row["parent_id"] in post_ids:
            return "COMMENT"
        if row["parent_id"] in comment_ids:
            return "REPLY"
        return "COMMENT"

    if not comments_df.empty:
        comments_df["TYPE"] = comments_df.apply(classify, axis=1)

        # Attach post context
        comments_df = comments_df.merge(
            posts_df[["post_id", "self_text"]],
            on="post_id",
            how="left"
        )

        # Attach parent comment context
        comments_df = comments_df.merge(
            comments_df[["comment_id", "body"]],
            left_on="parent_id",
            right_on="comment_id",
            how="left",
            suffixes=("", "_parent")
        )

        def context(row):
            return row["self_text"] if row["TYPE"] == "COMMENT" else row["body_parent"]

    # Format posts
    posts_fmt = pd.DataFrame({
        "PLATFORM": "Reddit",
        "ENTITY": subreddit_name,
        "DATE": pd.to_datetime(posts_df["created_utc"], unit="s").dt.strftime("%d-%m-%Y"),
        "TYPE": "POST",
        "ID": posts_df["post_id"],
        "DESCRIPTION": posts_df["self_text"].fillna(""),
        "PARENT_DESCRIPTION": posts_df["self_text"].fillna("")
    })

    # Format comments (if any)
    if not comments_df.empty:
        comments_fmt = pd.DataFrame({
            "PLATFORM": "Reddit",
            "ENTITY": subreddit_name,
            "DATE": pd.to_datetime(comments_df["created_utc"], unit="s").dt.strftime("%d-%m-%Y"),
            "TYPE": comments_df["TYPE"],
            "ID": comments_df["comment_id"],
            "DESCRIPTION": comments_df["body"],
            "PARENT_DESCRIPTION": comments_df.apply(context, axis=1)
        })
        final_df = pd.concat([posts_fmt, comments_fmt], ignore_index=True)
    else:
        final_df = posts_fmt

    return final_df

# =====================================================
# MAIN
# =====================================================
def main():
    reddit = get_reddit()

    posts_df, comments_df = fetch_data(reddit)

    if posts_df.empty:
        raise ValueError(
            "No posts found for the given subreddit and date range. "
            "Try widening the date range."
        )

    final_df = clean_data(posts_df, comments_df)

    subreddit = CONFIG["reddit"]["subreddit_name"]
    start = CONFIG["reddit"]["start_date"].replace("-", "")
    end = CONFIG["reddit"]["end_date"].replace("-", "")

    output_file = f"{subreddit}_cleaned_{start}_{end}.xlsx"
    final_df.to_excel(output_file, index=False)

    logging.info(f"Cleaned Excel file saved: {output_file}")


if __name__ == "__main__":
    main()
