import time
import pprint
import urlparse
import os

from celery import Celery
from flask_cache import Cache
from flask import Flask, render_template, request, g, jsonify

import scrapers
from forex_python.converter import CurrencyRates


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

broker_host = os.environ.get('BROKER_NAME', 'localhost')
broker_str = 'pyamqp://guest@{}:5672'.format(broker_host)
print 'BROKER: ', broker_str
celery = Celery('app', broker=broker_str,
                backend='rpc://')
cache = Cache(app, config={'CACHE_TYPE': 'filesystem',
                           'CACHE_DIR': 'cache'})


@app.template_filter('domain_name')
def domain_name(s):
    """Takes a URL and returns the domain portion"""
    return urlparse.urlparse(s).netloc


@cache.memoize(timeout=86400)
def get_exchange_rate(currency1, currency2):
    if currency1 == currency2:
        return 1
    c = CurrencyRates()
    return c.get_rate(currency1, currency2)


@celery.task
def search_task(scraper_name, manufacturer, length):
    scraper = scrapers.all_scrapers[scraper_name]()
    results = scraper.search_and_parse(manufacturer, length)
    # Convert currency to USD
    for result in results:
        if 'currency' not in result:
            continue
        exchange_rate = get_exchange_rate(result['currency'], 'USD')
        result['parsed_price'] = result['parsed_price'] * exchange_rate
    return results


def search_all(manufacturer, length):
    async_results = []
    for scraper_name in scrapers.all_scrapers.iterkeys():
        async_result = search_task.delay(scraper_name, manufacturer, length)
        async_results.append(async_result)
    return [a.task_id for a in async_results]


def get_all_results(task_ids):
    async_results = [search_task.AsyncResult(id) for id in task_ids]
    results = []
    timeout = time.time() + 30  # 10 second timeout
    for async_result in async_results:
        time_left = timeout - time.time()
        try:
            result = async_result.get(timeout=time_left)
        except Exception as e:
            print 'Exception for scraper:\n{}'.format(str(e))
            continue
            # import ipdb; ipdb.set_trace()
        results.extend(result)
    return results


def get_single_site_results(task_ids):
    async_results = {search_task.AsyncResult(id) for id in task_ids}
    timeout = time.time() + 20
    while time.time() < timeout:
        for async_result in async_results:
            if async_result.ready():
                task_ids.remove(async_result.task_id)
                if async_result.failed():
                    return [], list(task_ids)
                else:
                    return async_result.get(timeout=2), list(task_ids)
    raise Exception('Get Result timed out')


@app.route('/')
def home():
    num_scrapers = len(scrapers.all_scrapers)
    return render_template('home.html', num_scrapers=num_scrapers)


@app.route('/search/')
def search():
    if request.is_xhr:
        manufacturer = request.args['manufacturer'].strip()
        length = request.args['length'].strip()
        task_ids = search_all(manufacturer, length)
        return jsonify(task_ids=task_ids)
    else:
        return render_template('home.html')


@app.route('/search/results/', methods=['POST'])
def search_results():
    task_ids = request.get_json()['task_ids']
    results, remaining_task_ids = get_single_site_results(task_ids)
    return jsonify(results=results, task_ids=remaining_task_ids)


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
