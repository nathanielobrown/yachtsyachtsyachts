import re


from base_scraper import BaseScraper


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
        return p
