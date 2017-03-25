

from base_scraper import BaseScraper


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
