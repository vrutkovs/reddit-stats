from aiohttp import web, MsgType, WSCloseCode
import aiohttp_jinja2
import jinja2
import json
import traceback

from reddit_stats import prepare_db, get_reddit_text, convert_dates
from db import (
    get_top_post_authors, get_top_posts_karma, get_avg_posts_karma,
    get_top_comment_authors, get_avg_post_comments, get_avg_comments_karma,
    get_top_comment_karma, get_avg_comment_karma, get_worst_avg_comment_karma,
    get_popular_flairs, get_most_popular_posts, get_most_popular_comments,
    get_least_popular_comments, get_total_comments, get_total_users,
    get_total_posts, get_total_post_comments, set_thresholds)


async def root(request):
    return web.Response(text="Move along, nothing to see here")


@aiohttp_jinja2.template('subreddit.jinja2')
async def subreddit(request):
    return {'subreddit': request.match_info['subreddit']}


@aiohttp_jinja2.template('progress.jinja2')
async def progress(request):
    data = await request.post()
    request.app['from_date'] = data['from']
    request.app['to_date'] = data['to']
    request.app['post_threshold'] = int(data['post-touchspin'])
    request.app['comment_threshold'] = int(data['comment-touchspin'])

    set_thresholds(request.app['post_threshold'], request.app['comment_threshold'])

    # TODO: read this from request.app.router
    ws_url = '/{subreddit}/progress/ws'.format(subreddit=request.match_info['subreddit'])
    redirect_url = '/{subreddit}/report'.format(subreddit=request.match_info['subreddit'])
    return {
        'subreddit': request.match_info['subreddit'],
        'ws_url': ws_url,
        'redirect_url': redirect_url}


@aiohttp_jinja2.template('report.jinja2')
async def report(request):
    db = request.app['db']
    data = {
        'subreddit': request.match_info['subreddit'],
        'start_date': request.app['start_date'],
        'end_date': request.app['end_date'],
        'post_threshold': request.app['post_threshold'],
        'comment_threshold': request.app['comment_threshold'],
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
    reddit_text = get_reddit_text(aiohttp_jinja2.get_env(app), data)
    data['reddit_text'] = reddit_text
    return data


async def ws(request):
    sub_name = request.match_info['subreddit']
    ws = web.WebSocketResponse()
    request.app['websockets'].append(ws)
    await ws.prepare(request)
    async for msg in ws:
        if msg.tp == MsgType.text:
            from_date = request.app['from_date']
            to_date = request.app['to_date']
            request.app['start_date'], request.app['end_date'] = convert_dates(from_date, to_date)

            try:
                db = prepare_db(sub_name, from_date, to_date, ws)
                request.app['db'] = db
                ws.send_str(json.dumps({"done": ""}))
            except:
                data = {'error': traceback.format_exc()}
                ws.send_str(json.dumps(data))
    return ws


async def on_shutdown(app):
    for ws in app['websockets']:
        await ws.close(code=WSCloseCode.GOING_AWAY,
                       message='Server shutdown')


app = web.Application(debug=True)
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
app.router.add_static('/static/', path='static', show_index=True, follow_symlinks=True)

app.router.add_route('*', '/', root)
app.router.add_route('*', '/{subreddit}', subreddit)
app.router.add_route('*', '/{subreddit}/', subreddit)
app.router.add_route('POST', '/{subreddit}/progress', progress)
app.router.add_route('*', '/{subreddit}/progress/ws', ws)
app.router.add_route('*', '/{subreddit}/report', report)

app['websockets'] = []
app.on_shutdown.append(on_shutdown)

web.run_app(app)
