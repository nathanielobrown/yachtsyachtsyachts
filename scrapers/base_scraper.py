# -*- coding: utf-8 -*-
import io
import re
import urlparse
import uuid

from bs4 import BeautifulSoup
from PIL import Image
import imagehash
import requests

__version__ = '0.1'
# BeautifulSoup = functools.partial(bs4.BeautifulSoup, markup='html.parser')


class BaseScraper(object):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = ('Mozilla/5.0 (Macintosh; Intel '
            'Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/56.0.2924.87 Safari/537.36')

    def search(self, manufacturer=None, length=None):
        url = self.url.format(manufacturer=manufacturer, length=length)
        resp = self.session.get(url)
        assert resp.status_code == 200
        return resp.content

    def _result_post_processing(self, result):
        if 'image_url' in result and result['image_url']:
            result['image_url'] = self.process_url(result['image_url'])
            result['image_hash'] = self._make_image_hash(result['image_url'])
        else:
            result['image_url'] = None
            result['image_hash'] = uuid.uuid1().hex
        result['link'] = self.process_url(result['link'])
        if 'year' in result and result['year']:
            result['year'] = int(result['year'])
        result['title'] = self.clean_whitespace(result['title'])
        if 'price' in result and result['price']:
            price, currency = self.parse_price(result['price'])
            result['parsed_price'] = price
            result['currency'] = currency
        return result

    def _make_image_hash(self, image_url):
        resp = self.session.get(image_url)
        if resp.status_code != 200:
            raise Exception('bad_image_url : {}'.format(image_url))
        f = io.BytesIO(resp.content)
        img = Image.open(f)
        return str(imagehash.average_hash(img, hash_size=4))

    def parse_search_results(self, html):
        soup = BeautifulSoup(html, 'lxml')
        html_results = soup.select(self._results_css_selector)
        parsed_results = []
        for html_result in html_results:
            result = self._parse_result(html_result)
            if not result:
                continue
            result = self._result_post_processing(result)
            result['html'] = unicode(html_result)
            parsed_results.append(result)
        return parsed_results

    def search_and_parse(self, **kwargs):
        html = self.search(**kwargs)
        return self.parse_search_results(html)

    @staticmethod
    def clean_whitespace(s):
        return re.sub('\s+', ' ', s).strip()

    @classmethod
    def base_url(cls):
        parsed_url = urlparse.urlparse(cls.url)
        return '{}://{}'.format(parsed_url.scheme, parsed_url.netloc)

    @classmethod
    def domain(cls):
        parsed_url = urlparse.urlparse(cls.url)
        return parsed_url.netloc

    def process_url(self, url):
        url = url.strip()
        if url.startswith('http'):
            return url
        elif url.startswith('//'):
            parsed_url = urlparse.urlparse(self.url)
            return '{}:{}'.format(parsed_url.scheme, url)
        elif url.startswith('/'):
            return self.base_url() + url
        else:
            raise Exception('cannot resolve url for relative path {!r}')

    def parse_price(self, price_str):
        price_str = price_str.lower()
        groups = re.search('([\d\,\.]+)', price_str)
        price_str_snippet = groups.group(1).split('.')[0]
        price = int(''.join((c for c in price_str_snippet if c.isdigit())))
        mapping = {
            'GBP': [u'£', 'gbp', '&pound;'],
            'EUR': [u'€', 'eur', '&euro;'],
            'USD': ['$', 'usd']
        }
        for currency, symbols in mapping.iteritems():
            for symbol in symbols:
                if symbol in price_str:
                    price_currency = currency
                    break
            else:
                continue
            break
        else:
            # import ipdb; ipdb.set_trace()
            raise Exception('Could not parse currency type')
        return price, price_currency
