import datetime
import os
import pprint
import time
import urlparse

from flask import Flask, render_template, request, jsonify, g
from flask_cache import Cache
from raven.contrib.celery import register_signal, register_logger_signal
from raven.contrib.flask import Sentry
import flask_admin
from flask_admin.contrib.sqla import ModelView

import celery
import raven

from forex_python.converter import CurrencyRates
import scrapers
from data_access_layer import DataAccessLayer
import model as m


app = Flask(__name__)
app.secret_key = 'asdfasghrwgn;wedsvcihjo[arfe;qcinvprwoe;sadjkv'
app.config['TEMPLATES_AUTO_RELOAD'] = True

broker_host = os.environ.get('BROKER_NAME', 'localhost')
backend_host = os.environ.get('BACKEND_NAME', 'localhost')
db_conn_str = os.environ.get('DB_CONN_STR',
                             'postgresql+psycopg2://postgres@localhost:5433')
broker_str = 'pyamqp://guest@{}:5672'.format(broker_host)
sentry_dsn = 'https://a89cf42846224019b1a72f7c56aa2f6a:13a3e6fd' \
             '0da94e278060355bb60bb933@sentry.io/151954'
if backend_host:
    backend_str = 'redis://{}:6379'.format(backend_host)
else:
    backend_str = 'rpc://'

print 'DB_STR: ', db_conn_str
print 'BROKER: ', broker_str
print 'BACKEND: ', backend_str
dal = DataAccessLayer(db_conn_str)
dal.connect()
# dal.erase_database()
admin = flask_admin.Admin()
admin.init_app(app)
admin.add_view(ModelView(m.Search, dal.ScopedSession))
admin.add_view(ModelView(m.SearchResult, dal.ScopedSession))



@app.before_request
def before_request():
    g.db = dal.ScopedSession()


@app.teardown_request
def teardown_request(r):
    g.db.close()
    return r


class Celery(celery.Celery):

    def on_configure(self):
        client = raven.Client(sentry_dsn)

        # register a custom filter to filter out duplicate logs
        register_logger_signal(client)

        # hook into the Celery error handler
        register_signal(client)


celery = Celery('app', broker=broker_str,
                backend=backend_str)
celery.conf['task_track_started'] = True

cache = Cache(app, config={'CACHE_TYPE': 'filesystem',
                           'CACHE_DIR': 'cache'})
# sentry = Sentry(app, dsn=sentry_dsn)


@app.template_filter('domain_name')
def domain_name(s):
    """Takes a URL and returns the domain portion"""
    return urlparse.urlparse(s).netloc


@cache.memoize(timeout=86400)
def get_exchange_rate(currency1, currency2):
    if currency1 == currency2:
        return 1
    c = CurrencyRates()
    rate = c.get_rate(currency1, currency2)
    del c
    return rate


@celery.task
def search_task(scraper_name, manufacturer, length):
    session = dal.ScopedSession()
    # Check if we already have results for this
    stale_time = datetime.datetime.now() - datetime.timedelta(hours=1)
    q = session.query(m.Search).filter(m.Search.search_time > stale_time)
    q = q.filter_by(scraper_name=scraper_name)
    q = q.filter(m.Search.kwargs['manufacturer'].astext.cast(m.String) ==
                 manufacturer)
    q = q.filter(m.Search.kwargs['length'].astext.cast(m.String) == length)
    search = q.first()
    if search:
        print "Using 'dat cache!!!"
        results = [dict(result.parsed_results) for result in search.results]
        return results
    kwargs = {
        'manufacturer': manufacturer,
        'length': length
    }
    scraper = scrapers.all_scrapers[scraper_name]()
    search = m.Search(
        scraper_name=scraper_name,
        site_domain=scraper.domain(),
        kwargs=kwargs
    )
    results = scraper.search_and_parse(**kwargs)
    # Convert currency to USD
    for result in results:
        if 'currency' not in result:
            continue
        exchange_rate = get_exchange_rate(result['currency'], 'USD')
        result['parsed_price'] = result['parsed_price'] * exchange_rate
        html = result.pop('html')
        sr = m.SearchResult(
            html=html,
            parsed_results=result
        )
        search.results.append(sr)
    try:
        session.add(search)
    except Exception:
        session.rollback()
        raise()
    else:
        session.commit()
    finally:
        session.close()
    del scraper
    return results


def search_all(manufacturer, length):
    tasks = []
    for scraper_name, scraper in scrapers.all_scrapers.iteritems():
        args = (scraper_name, manufacturer, length)
        kwargs = {}
        async_result = search_task.apply_async(args=args, kwargs=kwargs)
        task = {
            "task_id": async_result.task_id,
            "status": "PENDING",
            "num_results": 0,
            "results": [],
            "note": None,
            "args": args,
            "kwargs": kwargs,
            "domain": scraper.domain()
        }
        tasks.append(task)
    return tasks


# def get_all_results(task_ids):
#     async_results = [search_task.AsyncResult(id) for id in task_ids]
#     results = []
#     timeout = time.time() + 30  # 10 second timeout
#     for async_result in async_results:
#         time_left = timeout - time.time()
#         try:
#             result = async_result.get(timeout=time_left)
#         except Exception as e:
#             print 'Exception for scraper:\n{}'.format(str(e))
#             continue
#             # import ipdb; ipdb.set_trace()
#         results.extend(result)
#     return results

class SearchTaskWrapper(object):
    def __init__(self, task):
        """task an either be a task_id or a task"""
        if isinstance(task, basestring):
            self.task_id = task
        else:
            import ipdb; ipdb.set_trace()
        self.async_result = search_task.AsyncResult(self.task_id)
        self.results = []
        self.note = None

    def __iter__(self):
        yield ("task_id", self.task_id)
        yield ("status", self.async_result.status)
        yield ("results", self.results)
        yield ("num_results", len(self.results))
        yield ("note", self.note)

    @property
    def status(self):
        return self.async_result.status

    def ready(self):
        return self.async_result.ready()

    def update_results(self):
        if not self.async_result.failed():
            self.results = self.async_result.get(timeout=2)


def get_some_site_results(task_ids, min_wait=1, max_wait=20):
    """Wait until we find either a success or a failure, then return the
    dictionary versions of all the task_wrappers, plus task_ids to be polled
    for future udpates"""
    task_ids = set(task_ids)
    timeout = time.time() + max_wait
    min_time = time.time() + min_wait
    task_wrappers = [SearchTaskWrapper(task_id) for task_id in task_ids]
    new_results = False
    while time.time() < timeout:
        for task_wrapper in task_wrappers:
            # print task_wrapper.status
            # Skip tasks that we've already resolved
            if task_wrapper.task_id not in task_ids:
                continue
            if task_wrapper.ready():
                new_results = True
                task_ids.remove(task_wrapper.task_id)
                task_wrapper.update_results()
        # Return if we've waited long enough and found some results
        if new_results and time.time() > min_time:
            return map(dict, task_wrappers), list(task_ids)
        time.sleep(.5)
    raise Exception('Get Result timed out')


@app.route('/')
def home():
    num_scrapers = len(scrapers.all_scrapers)
    return render_template('home.html', num_scrapers=num_scrapers)


@app.route('/error')
def error():
    return 1 / 0


@app.route('/search/')
def search():
    if request.is_xhr:
        manufacturer = request.args['manufacturer'].strip()
        length = request.args['length'].strip()
        searches = search_all(manufacturer, length)
        return jsonify(searches=searches)
    else:
        return render_template('home.html')


@app.route('/search/results/', methods=['POST'])
def search_results():
    task_ids = request.get_json()['task_ids']
    searches, remaining_task_ids = get_some_site_results(task_ids, min_wait=0)
    return jsonify(searches=searches, task_ids=remaining_task_ids)


@app.route('/search_raw/')
def search_raw():
    manufacturer = request.args['manufacturer'].strip()
    length = request.args['length'].strip()
    results = search_all(manufacturer, length)
    return '<pre>{}</pre>'.format(pprint.pformat(results))


@app.route('/clear_cache/')
def clear_cache():
    cache.clear()
    return 'Cache cleared.'


if __name__ == '__main__':
    app.run(debug=True)
