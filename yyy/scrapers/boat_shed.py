import math
import urllib.request
import urllib.parse
import urllib.error
import re

import requests
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


class BoatShedScraper(BaseScraper):
    _results_css_selector = "#SearchResults li"
    # NOTE: This query string is unorthodox. Length is a range given in
    # centimeters in a homemade format, read the custom search method
    url = (
        "http://www.boatshed.com/dosearch.php?rank=-raw_gbp_price&"
        "bq=%7B%22manufacturer%22%3A%5B%22{manufacturer}%22%5D%2C%22"
        "{length}"
    )

    def search(self, manufacturer=None, length=None):
        length = float(length)
        min_length = int(math.floor(30.48 * length))
        max_length = int(math.ceil(30.48 * length))
        length_str = 'boatdetails_loa":["{}..{}"]}}'.format(min_length, max_length)
        length_str = urllib.parse.quote(length_str)
        url = self.url.format(manufacturer=manufacturer, length=length_str)
        resp = self.session.get(url)
        return resp.content

    def _parse_result(self, r):
        p = {}
        a_tag = r.find("a")
        p["link"] = urllib.parse.urljoin("http://www.boatshed.com", a_tag.attrs["href"])
        p["title"] = self.clean_whitespace(a_tag.attrs["title"])
        subtitle = r.find(class_="searchview_strapline")
        if subtitle:
            p["title"] += ", " + subtitle.text
        p["image_url"] = r.find("img").attrs["src"]
        resp = requests.get(p["link"])
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.content, "lxml")
        main = soup.find(itemtype="http://schema.org/Product")
        labels = main("th")
        for label in labels:
            label_text = label.text.strip().rstrip(":").lower()
            label_value = label.findNext("td").text.strip()
            p[label_text] = label_value
        p["location"] = p.pop("lying")
        year_label = soup.find("strong", text=re.compile("Year"))
        p["year"] = int(year_label.parent.findNext("div").text.strip())
        return p
