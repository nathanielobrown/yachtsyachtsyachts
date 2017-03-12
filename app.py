import time

from celery import Celery
from flask_cache import Cache
from flask import Flask, render_template, request

import scrapers


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

celery = Celery('app', broker='pyamqp://guest@localhost:5672',
                backend='rpc://')
cache = Cache(app, config={'CACHE_TYPE': 'filesystem',
                           'CACHE_DIR': 'cache'})


@celery.task
def run_search(scraper_name, manufacturer, length):
    scraper = scrapers.all_scrapers[scraper_name]()
    return scraper.search_and_parse(manufacturer, length)


@cache.memoize(timeout=600)
def search_all(manufacturer, length):
    async_results = {}
    for scraper_name in scrapers.all_scrapers.iterkeys():
        async_result = run_search.delay(scraper_name, manufacturer, length)
        async_results[scraper_name] = (async_result)
    results = []
    timeout = time.time() + 30  # 10 second timeout
    for scraper_name, async_result in async_results.iteritems():
        time_left = timeout - time.time()
        try:
            result = async_result.get(timeout=time_left)
        except Exception as e:
            print 'Exception for {}\n{}'.format(scraper_name, str(e))
            continue
            # import ipdb; ipdb.set_trace()
        results.extend(result)
    return results


@app.route('/')
def home():
    num_scrapers = len(scrapers.all_scrapers)
    return render_template('home.html', num_scrapers=num_scrapers)


@app.route('/search/')
def search():
    t_start = time.time()
    manufacturer = request.args['manufacturer'].strip()
    length = request.args['length'].strip()
    results = search_all(manufacturer, length)
    elapsed_time = time.time() - t_start
    return render_template('results.html', results=results,
                           elapsed_time=elapsed_time)


@app.route('/clear_cache/')
def clear_cache():
    cache.clear()
    return 'Cache cleared.'


if __name__ == '__main__':
    app.run(debug=True)
