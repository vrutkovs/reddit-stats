import praw
import json

from datetime import datetime, timedelta
from time import sleep

from db import Post, User, Comment, get_db, NoResultFound


def get_reddit():
    r = praw.Reddit(user_agent='Reddit stats by /r/liberta team', site_name="liberta")
    r.read_only = True
    return r


def parse_submissions(db, sub, from_date, to_date, ws):
    ws_log(ws, "Parsing submissions for {}".format(sub))

    week_delta = timedelta(weeks=1)
    UTC_OFFSET_TIMEDELTA = datetime.now() - datetime.utcnow()

    start_datetime = datetime.strptime(from_date, '%m/%d/%Y') + UTC_OFFSET_TIMEDELTA
    end_datetime = datetime.strptime(to_date, '%m/%d/%Y') + UTC_OFFSET_TIMEDELTA

    # Split timestamps into weeks
    timestamps = [start_datetime]
    while True:
        new_datetime = timestamps[-1] + week_delta
        timestamps[-1] = int(timestamps[-1].timestamp())
        timestamps.append(new_datetime)
        if new_datetime > end_datetime:
            timestamps[-1] = int(end_datetime.timestamp())
            break

    submissions = set()
    # Search for submissions by searching between timestamps
    for i in range(0, len(timestamps) - 1):
        search_term = 'timestamp:{}..{}'.format(timestamps[i]+1, timestamps[i+1])
        ws_log(ws, "Searching '{}'".format(search_term))
        new_posts = list(sub.search(search_term, sort='new', limit=1000))

        ws_log(ws, "Fetched {} submissions".format(len(new_posts)))
        if len(new_posts) > 0:
            last_post = new_posts[-1]
            last_post_date = datetime.utcfromtimestamp(last_post.created_utc).date()
            ws_log(ws, "Last post in the chunk is {} at {}".format(last_post.id, str(last_post_date)))

        submissions |= set(new_posts)

    total = len(submissions)
    ws_log(ws, "Found {} submissions".format(total))
    for i, submission in enumerate(submissions):
        add_post(db, submission)

        while True:
            try:
                submission.comments.replace_more(limit=0)
                break
            except:
                sleep(10)
        for comment in submission.comments.list():
            add_comment(db, submission.id, comment)

        progress = int(float((i+1)/total) * 100)
        ws_log(ws, "Parsed post {}".format(submission.id), progress)


def get_or_create_author(db, name):
    try:
        author = db.query(User).filter_by(name=name).one()
    except NoResultFound:
        author = User(name=name)
        db.add(author)
        db.commit()
    finally:
        return author


def add_post(db, submission):
    post_author = get_or_create_author(db, submission.author.name)

    post = Post()
    post.post_id = submission.id
    post.author = post_author
    post.title = submission.title
    post.score = submission.score
    post.flair = submission.link_flair_text
    post.num_comments = submission.num_comments
    post.full_link = "https://www.reddit.com{}".format(
        submission.permalink.replace('?ref=search_posts', ''))
    db.add(post)
    db.commit()


def add_comment(db, post_id, praw_comment):
    if not praw_comment.author:
        return

    comment_author = get_or_create_author(db, praw_comment.author.name)

    comment = Comment()
    comment.comment_id = praw_comment.id
    comment.author = comment_author
    comment.score = praw_comment.score
    comment.post_id = post_id
    db.add(comment)
    db.commit()


def ws_log(ws=None, message=None, progress=None):
    data = {}
    if progress:
        data['progress'] = progress
    data['log'] = message
    if ws:
        return ws.send_str(json.dumps(data))
    else:
        print(message)


def prepare_db(sub_name, from_date, to_date, ws=None):
    db = get_db()

    subreddit = get_reddit().subreddit(sub_name)
    parse_submissions(db, subreddit, from_date, to_date, ws)

    return db


def get_reddit_text(jinja_env, data, language='ru'):
    template = jinja_env.get_template('{}/reddit_report.jinja2'.format(language))
    return template.render(**data)


def convert_dates(from_date, to_date):
    return (datetime.strptime(from_date, '%m/%d/%Y').date(),
            datetime.strptime(to_date, '%m/%d/%Y').date())
