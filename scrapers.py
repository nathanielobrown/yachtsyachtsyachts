# -*- coding: utf-8 -*-
import io
import math
import re
import urllib
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

    def search(self, manufacturer, length):
        url = self.url.format(manufacturer=manufacturer, length=length)
        resp = self.session.get(url)
        return resp.content

    def _result_post_processing(self, result):
        if 'image_url' in result and result['image_url']:
            result['image_url'] = self.process_url(result['image_url'])
            result['image_hash'] = self._make_image_hash(result['image_url'])
        else:
            result['image_url'] = None
            result['image_hash'] = uuid.uuid1().hex
        result['link'] = self.process_url(result['link'])
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
        results = soup.select(self._results_css_selector)
        parsed_results = map(self._parse_result, results)
        processed_results = map(self._result_post_processing, parsed_results)
        return processed_results

    def search_and_parse(self, *args, **kwargs):
        html = self.search(*args, **kwargs)
        return self.parse_search_results(html)

    @staticmethod
    def clean_whitespace(s):
        return re.sub('\s+', ' ', s).strip()

    def base_url(self):
        parsed_url = urlparse.urlparse(self.url)
        return '{}://{}'.format(parsed_url.scheme, parsed_url.netloc)

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


class ApolloDuckScraper(BaseScraper):
    _results_css_selector = '.FeatureAdPanel, .StandardAdPanel'
    # TODO lookup IDs for manufacture and length
    url = 'https://www.apolloduck.com/boats.phtml?id=848&mi=2381'

    def search_and_parse(self, manufacturer, length):
        # Only works for contessa 32 now
        if manufacturer.lower() == 'contessa' and float(length) == 32:
            return super(ApolloDuckScraper, self).search_and_parse(manufacturer,
                                                             length)
        else:
            return []

    @staticmethod
    def _parse_result(r):
        p = {}
        p['title'] = r(class_=re.compile('.*Title$'))[0].text.strip()
        p['image_url'] = r.select('.PanelImage img')[0].attrs['src']
        labels = r.select('.PanelSpecLabel')
        p['link'] = r.select('.PanelImage a')[0].attrs['href']
        if not p['link'].startswith('http'):
            p['link'] = 'https://www.apolloduck.com' + p['link']
        for label in labels:
            label_text = label.text.strip().rstrip(':').lower()
            label_value = label.findNext(class_='PanelSpecData').text.strip()
            p[label_text] = label_value
        p['year'] = int(p['year'])
        return p


class YachtWorldScraper(BaseScraper):
    _results_css_selector = '.searchResultDetailsContainer .listing'
    url = ("http://www.yachtworld.com/core/listing/cache/searchResults.jsp"
          "?man={manufacturer}&is=&type=&luom=126&fromLength={length}&"
          "toLength={length}&fromYear=&toYear=&pricderange=Select+Price+"
          "Range&Ntt=&fromPrice=0&toPrice=&searchtype=homepage&cit=true&"
          "slim=quick&ybw=&sm=3&Ntk=boatsEN&currencyid=100&ps=50")

    def _parse_result(self, r):
        p = {}
        p['price'] = r.find(class_='price').text.strip()
        p['location'] = self.clean_whitespace(r.find(class_='location').text)
        p['image_url'] = r.find('img').attrs['src']
        a_tag = r.find(class_='make-model').find('a')
        p['link'] = 'http://www.yachtworld.com' + a_tag.attrs['href']
        p['title'] = self.clean_whitespace(a_tag.text)
        p['year'] = int(re.search('\d\d\d\d', p['title']).group())
        # import ipdb; ipdb.set_trace()
        return p


class Boatshop24Scraper(BaseScraper):
    _results_css_selector = '.latest_ads_list .ad-list.item'
    url = ("http://www.boatshop24.co.uk/sailing?sstr={manufacturer}%20"
           "{length}")

    def _parse_result(self, r):
        p = {}
        a_tag = r.find(class_='title').find('a')
        p['link'] = 'http://www.boatshop24.co.uk' + a_tag.attrs['href']
        p['title'] = self.clean_whitespace(a_tag.text)
        p['price'] = next(r.find(class_='price').children)
        labels = r('td', class_='label')
        for label in labels:
            label_text = label.text.strip().rstrip(':').lower()
            label_value = label.findNext('td').text.strip()
            p[label_text] = label_value
        p['year'] = int(p.pop('year built'))
        resp = requests.get(p['link'])
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.content, 'lxml')
        p['location'] = soup.find(class_='location').text
        p['image_url'] = r.find('img').attrs['src']
        return p


class TheYachtMarketScraper(BaseScraper):
    _results_css_selector = '.search-results .result'
    url = ("http://www.theyachtmarket.com/boatsearchresults.aspx?"
           "manufacturermodel={manufacturer}&currency=gbp&lengthfrom={length}&"
           "lengthto={length}&lengthunit=feet&saleorcharter=sale")

    def _parse_result(self, r):
        p = {}
        a_tag = r.find('a', class_='boat-name')
        p['link'] = 'http://www.theyachtmarket.com' + a_tag.attrs['href']
        p['title'] = self.clean_whitespace(a_tag.text)
        p['location'] = self.clean_whitespace(r.find(class_='location').text)
        p['price'] = r.find(class_='pricing').text
        p['year'] = int(r.find(class_='overview').text[:4])
        p['image_url'] = r.find('img').attrs['src']
        return p


class BoatShedScraper(BaseScraper):
    _results_css_selector = '#SearchResults li'
    # NOTE: This query string is unorthodox. Length is a range given in
    # centimeters in a homemade format, read the custom search method
    url = ("http://www.boatshed.com/dosearch.php?rank=-raw_gbp_price&"
           "bq=%7B%22manufacturer%22%3A%5B%22{manufacturer}%22%5D%2C%22"
           "{length}")

    def search(self, manufacturer, length):
        length = float(length)
        min_length = int(math.floor(30.48 * length))
        max_length = int(math.ceil(30.48 * length))
        length_str = 'boatdetails_loa":["{}..{}"]}}'.format(min_length,
                                                           max_length)
        length_str = urllib.quote(length_str)
        url = self.url.format(manufacturer=manufacturer, length=length_str)
        resp = self.session.get(url)
        return resp.content

    def _parse_result(self, r):
        p = {}
        a_tag = r.find('a')
        p['link'] = 'http://www.boatshed.com' + a_tag.attrs['href']
        p['title'] = self.clean_whitespace(a_tag.attrs['title'])
        p['title'] += ', ' + r.find(class_='searchview_strapline').text
        p['image_url'] = r.find('img').attrs['src']
        resp = requests.get(p['link'])
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.content, "lxml")
        main = soup.find(itemtype="http://schema.org/Product")
        labels = main('th')
        for label in labels:
            label_text = label.text.strip().rstrip(':').lower()
            label_value = label.findNext('td').text.strip()
            p[label_text] = label_value
        p['location'] = p.pop('lying')
        p['year'] = int(p['year'])
        return p


class BoatsScraper(BaseScraper):
    _results_css_selector = '#search-results > div.boat-listings li'
    url = ("http://www.boats.com/boats-for-sale/?make={manufacturer}&"
           "length-from={length}&length-to={length}&uom=ft&"
           "currency=usd")

    def _parse_result(self, r):
        p = {}
        a_tag = r.find('a')
        p['link'] = self.base_url() + a_tag.attrs['href']
        p['title'] = r.find('h2').text.strip()
        p['location'] = r.find(class_='country').text.strip()
        p['year'] = int(r.find(class_='year').text.strip())
        p['price'] = r.find(class_='price').text.strip()
        p['image_url'] = r.find('img').attrs['src']
        return p


class ScanBoat(BaseScraper):
    _results_css_selector = 'div.pageContent a'
    url = ("https://www.scanboat.com/en/boats?SearchCriteria.BoatModelText="
           "{manufacturer}+{length}&SearchCriteria.BoatTypeID=0&"
           "SearchCriteria.Searched=true&SearchCriteria.ExtendedSearch=False")

    def _parse_result(self, r):
        p = {}
        p['link'] = self.base_url() + r.attrs['href']
        p['title'] = self.clean_whitespace(r.find('h2').text)
        p['price'] = self.clean_whitespace(r.find(class_='lbl').text)
        specifications = r.find(class_='specifications').text
        groups = re.search('Year\s*:\s*(\d\d\d\d)', specifications)
        p['year'] = int(groups.group(1))
        groups = re.search('Country\s*:\s*(.*?)\s*$', specifications)
        p['location'] = groups.group(1)
        p['engine'] = self.clean_whitespace(
            r.find(class_='engineSpecifications').text
        )
        p['image_url'] = r.find('img').attrs['src']
        return p


class CO32Scraper(BaseScraper):
    _results_css_selector = 'table tbody tr'
    url = 'http://www.co32.org/boats-for-sale'

    def search_and_parse(self, manufacturer, length):
        # This site is only for Contessa 32's, so no need to search if that's
        # not what we are looking for
        if manufacturer.lower() == 'contessa' and float(length) == 32:
            return super(CO32Scraper, self).search_and_parse(manufacturer,
                                                             length)
        else:
            return []

    def _parse_result(self, r):
        p = {}
        p['link'] = r.find('a').attrs['href']
        p['image_url'] = r.find('img').attrs['src']
        p['name'] = r.find(class_='views-field-title').text.strip()
        p['location'] = r.find(class_='field--location').text.strip()
        p['year'] = r.find(class_='field--year').text.strip()
        p['price'] = r.find(class_='field--price').text.strip()
        p['title'] = u'Contessa 32, {}'.format(p['name'])
        return p


class SailBoatListingsScraper(BaseScraper):
    _results_css_selector = 'table[width="100%"] table[cellspacing="1"]'
    url = ('http://www.sailboatlistings.com/cgi-bin/saildata/db.cgi?db='
           'default&uid=default&sb=33&so=descend&websearch=1&'
           'manufacturer={manufacturer}&model=&length-gt={length}&'
           'length-lt={length}&year-lt=---&year-gt=---&price-lt=&type=---&'
           'material=---&hull=---&state=&view_records=+Show+Matching+Boats+')

    def _parse_result(self, r):
        p = {}
        image_tag = r.find('img')
        if image_tag:
            p['image_url'] = image_tag.attrs['src']
        else:
            p['image_url'] = None
        p['link'] = r.find('a').attrs['href']
        p['title'] = r.find(class_='sailheader').text.strip()
        labels = r(class_='sailvb')
        for label in labels:
            label_text = label.text.strip().rstrip(':').lower()
            label_value = label.findNext(class_='sailvk').text.strip()
            p[label_text] = label_value
        p['price'] = p.pop('asking', None)
        assert 'year' in p
        assert 'location' in p
        return p

all_scrapers = {name: Scraper for name, Scraper in locals().iteritems()
            if isinstance(Scraper, type) and
            issubclass(Scraper, BaseScraper) and
            Scraper != BaseScraper}
