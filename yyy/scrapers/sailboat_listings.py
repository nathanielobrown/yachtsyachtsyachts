

from .base_scraper import BaseScraper


class SailBoatListingsScraper(BaseScraper):
    _results_css_selector = 'table[width="100%"] table[cellspacing="1"]'
    url = (
        "http://www.sailboatlistings.com/cgi-bin/saildata/db.cgi?db="
        "default&uid=default&sb=33&so=descend&websearch=1&"
        "manufacturer={manufacturer}&model=&length-gt={length}&"
        "length-lt={length}&year-lt=---&year-gt=---&price-lt=&type=---&"
        "material=---&hull=---&state=&view_records=+Show+Matching+Boats+"
    )

    def _parse_result(self, r):
        p = {}
        image_tag = r.find("img")
        if image_tag:
            p["image_url"] = image_tag.attrs["src"]
        else:
            p["image_url"] = None
        a_tag = r.find("a")
        if not a_tag:
            return None
        p["link"] = a_tag.attrs["href"]
        tag = r.find(class_="sailheader")
        if not tag:
            return None
        p["title"] = tag.text.strip()
        labels = r(class_="sailvb")
        for label in labels:
            label_text = label.text.strip().rstrip(":").lower()
            label_value = label.findNext(class_="sailvk").text.strip()
            p[label_text] = label_value
        p["price"] = p.pop("asking", None)
        # assert 'year' in p
        # assert 'location' in p
        return p
