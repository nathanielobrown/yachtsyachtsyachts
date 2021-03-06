

from .base_scraper import BaseScraper


class CO32Scraper(BaseScraper):
    _results_css_selector = "table tbody tr"
    url = "http://www.co32.org/boats-for-sale"

    def search_and_parse(self, manufacturer=None, length=None):
        # This site is only for Contessa 32's, so no need to search if that's
        # not what we are looking for
        if manufacturer.lower() == "contessa" and str(length.strip()) == "32":
            return super(CO32Scraper, self).search_and_parse(
                manufacturer=manufacturer, length=length
            )
        else:
            return []

    def _parse_result(self, r):
        p = {}
        p["link"] = r.find("a").attrs["href"]
        img = r.find("img")
        if img:
            p["image_url"] = img.attrs["src"]
        else:
            p["image_url"] = self.image_not_found_url
        p["name"] = r.find(class_="views-field-title").text.strip()
        p["location"] = r.find(class_="field--location").text.strip()
        year = r.find(class_="field--year")
        if year:
            p["year"] = year.text.strip()
        p["price"] = r.find(class_="field--price").text.strip()
        p["title"] = "Contessa 32, {}".format(p["name"])
        return p
