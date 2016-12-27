from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

from db import (
    get_db,
    get_top_post_authors, get_top_posts_karma, get_avg_posts_karma,
    get_top_comment_authors, get_avg_post_comments, get_avg_comments_karma,
    get_top_comment_karma, get_avg_comment_karma, get_worst_avg_comment_karma,
    get_popular_flairs, get_most_popular_posts, get_most_popular_comments,
    get_least_popular_comments, get_total_comments, get_total_users,
    get_total_posts, get_total_post_comments)

from reddit_stats import get_reddit, parse_submissions, get_reddit_text

SUBREDDIT_TO_POST = 'bottesting'
SUBREDDIT_TO_ANALYZE = 'liberta'
LANGUAGE = 'ru'
post_threshold = 3
comment_threshold = 5

to_date = datetime.utcnow().date() - timedelta(weeks=1)
from_date = to_date - timedelta(weeks=1)
to_date_str = to_date.strftime('%m/%d/%Y')
from_date_str = from_date.strftime('%m/%d/%Y')

db = get_db()
subreddit = get_reddit().subreddit(SUBREDDIT_TO_ANALYZE)
parse_submissions(db, subreddit, from_date_str, to_date_str, None)

jinja_env = Environment(loader=FileSystemLoader('templates'))
data = {
    'subreddit': SUBREDDIT_TO_ANALYZE,
    'start_date': from_date,
    'end_date': to_date,
    'post_threshold': post_threshold,
    'comment_threshold': comment_threshold,
    'total_posts': get_total_posts(db),
    'total_comments': get_total_comments(db),
    'total_users': get_total_users(db),
    'top_post_authors': get_top_post_authors(db),
    'total_posts_karma': get_top_posts_karma(db),
    'avg_posts_karma': get_avg_posts_karma(db),
    'total_post_comments': get_total_post_comments(db),
    'top_comment_authors': get_top_comment_authors(db),
    'avg_post_comments': get_avg_post_comments(db),
    'avg_comments_karma': get_avg_comments_karma(db),
    'top_comment_karma': get_top_comment_karma(db),
    'avg_comment_karma': get_avg_comment_karma(db),
    'worst_avg_comment_karma': get_worst_avg_comment_karma(db),
    'popular_flairs': get_popular_flairs(db),
    'most_popular_posts': get_most_popular_posts(db),
    'most_popular_comments': get_most_popular_comments(db),
    'least_popular_comments': get_least_popular_comments(db)
}
text_to_post = get_reddit_text(jinja_env, data, LANGUAGE)

reddit = get_reddit()
reddit.read_only = False
reddit.subreddit(SUBREDDIT_TO_POST).submit('/r/liberta report', text_to_post)
print("Report was posted")
