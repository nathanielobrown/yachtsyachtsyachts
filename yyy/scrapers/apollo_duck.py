import re


from .base_scraper import BaseScraper


class ApolloDuckScraper(BaseScraper):
    """
    apolloduck.com has a crappy, free form google search that can then be
    refined with filters. This does not return very many results.

    You can also select by manufacturer and then length/model, which returns
    more results.
    """

    _results_css_selector = ".FeatureAdPanel, .StandardAdPanel"
    # TODO lookup IDs for manufacture and length
    url = "https://www.apolloduck.com/boats.phtml?id=848&mi=2381"

    def search(self, manufacturer=None, length=None):
        # Get available manufacturers
        resp = self.session.get("https://www.apolloduck.com/brands.phtml")
        assert resp.status_code == 200
        matches = re.findall('href="/boats/(.+?)">(.*?)<', resp.text)
        manufacturer_ids = {
            make.lower().strip(): id.strip() for id, make in matches
        }
        assert len(manufacturer_ids) > 0
        if manufacturer.lower() in manufacturer_ids:
            manufacturer_id = manufacturer_ids[manufacturer.lower()]
        else:
            # Fall back to freeform search
            print(
                "Could not find manufacturer {}, falling back to freeform"
                " search".format(manufacturer)
            )
            return self.google_search(manufacturer, length)
        url = "https://www.apolloduck.com/boats/{}".format(
            manufacturer_id
        )
        resp = self.session.get(url)
        assert resp.status_code == 200
        matches = re.findall(f'/boats/{manufacturer_id}/(\d+)">(.*?)<', resp.text)
        model_ids = {model.lower().strip(): int(id.strip()) for id, model in matches}
        if str(length) in model_ids:
            model_id = model_ids[str(length)]
        else:
            # Fall back to freeform search
            print(
                "Could not find model {}, for manufacturer {} falling back "
                "to freeform".format(length, manufacturer)
            )
            return self.google_search(manufacturer, length)
        url = "https://www.apolloduck.com/boats/{}/{}?limit=100".format(
            manufacturer_id, model_id
        )
        resp = self.session.get(url)
        assert resp.status_code == 200
        return resp.content

    def google_search(self, manufacturer, length):
        raise Exception("not implimented")

    def _parse_result(self, r):
        p = {}
        p["title"] = r(class_=re.compile(".*Title$"))[0].text.strip()
        img = r.select(".PanelImage img")
        if img:
            p["image_url"] = img[0].attrs["src"]
        else:
            p["image_url"] = self.image_not_found_url
        labels = r.select(".PanelSpecLabel")
        p["link"] = r.select(".PanelImage a, a.FeatureTitle")[0].attrs["href"]
        if not p["link"].startswith("http"):
            p["link"] = "https://www.apolloduck.com" + p["link"]
        for label in labels:
            label_text = label.text.strip().rstrip(":").lower()
            label_value = label.findNext(class_="PanelSpecData").text.strip()
            p[label_text] = label_value
        p["year"] = int(p["year"])
        return p
