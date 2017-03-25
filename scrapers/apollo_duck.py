import re


from base_scraper import BaseScraper


class ApolloDuckScraper(BaseScraper):
    _results_css_selector = '.FeatureAdPanel, .StandardAdPanel'
    # TODO lookup IDs for manufacture and length
    url = 'https://www.apolloduck.com/boats.phtml?id=848&mi=2381'

    def search_and_parse(self, manufacturer, length):
        # Only works for contessa 32 now
        if manufacturer.lower() == 'contessa' and float(length) == 32:
            base = super(ApolloDuckScraper, self)
            return base.search_and_parse(manufacturer, length)
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