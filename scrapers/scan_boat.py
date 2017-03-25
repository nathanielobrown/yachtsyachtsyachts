import re


from base_scraper import BaseScraper


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
