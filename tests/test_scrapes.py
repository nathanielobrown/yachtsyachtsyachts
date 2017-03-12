import unittest
import os
import sys
import pprint

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import scrapers


class BaseTest(unittest.TestCase):
    pass


class TestScrapers(BaseTest):
    """Groups scrapes tests. The individual tests are added dynamically"""
    pass


for name, Scraper in scrapers.all_scrapers.iteritems():
    def wrapper(name, Scraper):
        def test(self):
            scraper = Scraper()
            html = scraper.search('contessa', '32')
            parsed_results = scraper.parse_search_results(html)
            self.assertGreater(len(parsed_results), 0)
            pprint.pprint(parsed_results)
        return test
    f = wrapper(name, Scraper)
    f.func_name = 'test_' + name
    print f.func_name
    setattr(TestScrapers, f.func_name, f)
del f


if __name__ == '__main__':
    print 'testing....'
    unittest.main()
