from sqlalchemy import ForeignKey, Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm.exc import NoResultFound

from collections import OrderedDict

POST_THRESHOLD = 0
COMMENT_THRESHOLD = 0

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")


class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    post_id = Column(String, unique=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")
    flair = Column(String)
    score = Column(Integer)
    num_comments = Column(Integer)
    comments = relationship("Comment", back_populates="post")
    full_link = Column(String)


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    comment_id = Column(String, unique=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="comments")
    post_id = Column(Integer, ForeignKey('posts.post_id'))
    post = relationship("Post", back_populates="comments")
    score = Column(Integer)


def get_db():
    engine = create_engine('sqlite://')
    #engine = create_engine('sqlite:///reddit.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def set_thresholds(post, comment):
    global POST_THRESHOLD
    POST_THRESHOLD = int(post)
    global COMMENT_THRESHOLD
    COMMENT_THRESHOLD = int(comment)


def get_total_posts(db):
    return db.query(Post.id).count()


def get_total_comments(db):
    return db.query(Comment.id).count()


def get_total_users(db):
    return db.query(User.id).count()


def get_top_comment_authors(db):
    comment_count_func = func.count(Comment.id).label('comment_count')
    query = db.query(User.name, comment_count_func).\
        filter(User.id == Comment.author_id).\
        group_by(Comment.author_id).\
        having(comment_count_func >= COMMENT_THRESHOLD).\
        order_by(comment_count_func.desc()).\
        limit(10)

    return OrderedDict([(u, c) for u, c in query])


def get_avg_post_comments(db):
    posts_count_func = func.count(Post.id).label('post_count')

    avg_func = func.avg(Post.num_comments).label('avg_comments')
    stmt = db.query(Post.author_id, posts_count_func, avg_func).\
        group_by(Post.author_id).\
        having(posts_count_func >= POST_THRESHOLD).\
        subquery()
    query = db.query(User.name, stmt.c.avg_comments).\
        filter(stmt.c.avg_comments != None).\
        outerjoin(stmt, User.id == stmt.c.author_id).\
        order_by(stmt.c.avg_comments.desc()).\
        limit(10)

    return OrderedDict([(u, "{0:.2f}".format(c)) for u, c in query])


def get_avg_comments_karma(db):
    comment_count_func = func.count(Comment.id).label('comment_count')
    avg_func = func.avg(Comment.score).label('karma_avg')

    stmt = db.query(Comment.author_id, comment_count_func, avg_func).\
        group_by(Comment.author_id).\
        having(comment_count_func >= COMMENT_THRESHOLD).\
        subquery()
    query = db.query(User.name, stmt.c.karma_avg).\
        filter(stmt.c.karma_avg != None).\
        outerjoin(stmt, User.id == stmt.c.author_id).\
        order_by(stmt.c.karma_avg.desc()).\
        limit(10)

    return OrderedDict([(u, "{0:.2f}".format(c)) for u, c in query])


def get_top_comment_karma(db):
    comment_count_func = func.count('*').label('comment_count')
    comment_sum_func = func.sum(Comment.score).label('comment_sum')
    stmt = db.query(Comment.author_id, comment_count_func, comment_sum_func).\
        group_by(Comment.author_id).\
        having(comment_count_func >= COMMENT_THRESHOLD).\
        subquery()
    query = db.query(User.name, stmt.c.comment_sum).\
        outerjoin(stmt, User.id == stmt.c.author_id).\
        order_by(stmt.c.comment_sum.desc()).\
        limit(10)

    return OrderedDict([(u, c) for u, c in query])


def get_avg_comment_karma(db):
    avg_func = func.sum(Comment.score).label('karma_avg')
    stmt = db.query(Comment.author_id, avg_func).\
        group_by(Comment.author_id).\
        having(avg_func >= COMMENT_THRESHOLD).\
        subquery()
    query = db.query(User.name, stmt.c.karma_avg).\
        filter(stmt.c.karma_avg != None).\
        outerjoin(stmt, User.id == stmt.c.author_id).\
        order_by(stmt.c.karma_avg.desc()).\
        limit(10)

    return OrderedDict([(u, c) for u, c in query])


def get_worst_avg_comment_karma(db):
    comment_count_func = func.count(Comment.id).label('comment_count')
    avg_func = func.sum(Comment.score).label('karma_avg')

    stmt = db.query(Comment.author_id, avg_func, comment_count_func).\
        group_by(Comment.author_id).\
        having(comment_count_func >= COMMENT_THRESHOLD).\
        subquery()
    query = db.query(User.name, stmt.c.karma_avg).\
        filter(stmt.c.karma_avg != None).\
        outerjoin(stmt, User.id == stmt.c.author_id).\
        order_by(stmt.c.karma_avg.asc()).\
        limit(10)

    return OrderedDict([(u, c) for u, c in query])


def get_popular_flairs(db):
    flair_sum_func = func.count('*').label('flair_sum')
    query = db.query(Post.flair, flair_sum_func).\
        group_by(Post.flair).\
        order_by(flair_sum_func.desc()).\
        limit(10)

    return OrderedDict([(u, c) for u, c in query])


def get_top_post_authors(db):
    stmt = db.query(Post.author_id, func.count('*').label('post_count')).\
        group_by(Post.author_id).subquery()
    query = db.query(User.name, stmt.c.post_count).\
        outerjoin(stmt, User.id == stmt.c.author_id).\
        order_by(stmt.c.post_count.desc()).\
        limit(10)

    return OrderedDict([(u, c) for u, c in query])


def get_top_posts_karma(db):
    stmt = db.query(Post.author_id, func.sum(Post.score).label('karma_sum')).\
        group_by(Post.author_id).subquery()
    query = db.query(User.name, stmt.c.karma_sum).\
        outerjoin(stmt, User.id == stmt.c.author_id).\
        order_by(stmt.c.karma_sum.desc()).\
        limit(10)

    return OrderedDict([(u, c) for u, c in query])


def get_avg_posts_karma(db):
    posts_count_func = func.count(Post.id).label('posts_count')
    karma_avg_func = func.avg(Post.score).label('karma_avg')

    stmt = db.query(Post.author_id, karma_avg_func, posts_count_func).\
        group_by(Post.author_id).\
        having(posts_count_func >= POST_THRESHOLD).\
        subquery()
    query = db.query(User.name, stmt.c.karma_avg).\
        filter(stmt.c.karma_avg != None).\
        outerjoin(stmt, User.id == stmt.c.author_id).\
        order_by(stmt.c.karma_avg.desc()).\
        limit(10)

    return OrderedDict([(u, "{0:.2f}".format(c)) for u, c in query])


def get_total_post_comments(db):
    posts_count_func = func.count(Post.id).label('post_count')
    sum_func = func.sum(Post.num_comments).label('sum_comments')

    stmt = db.query(Post.author_id, posts_count_func, sum_func).\
        group_by(Post.author_id).\
        having(posts_count_func >= POST_THRESHOLD).\
        subquery()
    query = db.query(User.name, stmt.c.sum_comments).\
        outerjoin(stmt, User.id == stmt.c.author_id).\
        order_by(stmt.c.sum_comments.desc()).\
        limit(10)

    return OrderedDict([(u, c) for u, c in query])


def get_most_popular_posts(db):
    query = db.query(Post.title, Post.post_id, Post.score).\
        order_by(Post.score.desc()).\
        limit(10)

    result = OrderedDict()
    for title, id, score in query:
        formatted_name = '[{}](https://redd.it/{})'.format(title, id)
        #result[formatted_name] = score
        result[id] = {'title': title, 'id': id, 'score': score}

    return result


def get_most_popular_comments(db):
    query = db.query(User.name, Post.full_link, Comment.comment_id, Comment.score).\
        filter(User.id == Comment.author_id).\
        filter(Post.post_id == Comment.post_id).\
        order_by(Comment.score.desc()).\
        limit(10)

    result = OrderedDict()
    for user, post_link, comment_id, score in query:
        #formatted_name = '[{}]({}{})'.format(user, post_link, comment_id)
        #result[formatted_name] = score
        result[comment_id] = {'user': user, 'post_link': post_link, 'score': score}

    return result


def get_least_popular_comments(db):
    query = db.query(User.name, Post.full_link, Comment.comment_id, Comment.score).\
        filter(User.id == Comment.author_id).\
        filter(Post.post_id == Comment.post_id).\
        order_by(Comment.score.asc()).\
        limit(10)

    result = OrderedDict()
    for user, post_link, comment_id, score in query:
        #formatted_name = '[{}]({}{})'.format(user, post_link, comment_id)
        #result[formatted_name] = score
        result[comment_id] = {'user': user, 'post_link': post_link, 'score': score}

    return result
