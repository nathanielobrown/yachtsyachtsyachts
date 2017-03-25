

from base_scraper import BaseScraper


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
