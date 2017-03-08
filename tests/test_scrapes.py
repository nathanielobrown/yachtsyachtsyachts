import unittest
import os
import sys
import pprint

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import scrapers


class BaseTest(unittest.TestCase):
    pass


# class TestApolloScraper(BaseTest):
#     def setUp(self):
#         self.scraper = scrapers.ApolloDuckScraper()

#     def test_search_and_parse(self):
#         html = self.scraper.search()
#         parsed_results = self.scraper.parse_search_results(html)
#         self.assertGreater(len(parsed_results), 0)
#         pprint.pprint(parsed_results)


# class TestYachtWorldScraper(BaseTest):
#     def setUp(self):
#         self.scraper = scrapers.Yach()

#     def test_search_and_parse(self):
#         html = self.scraper.search()
#         parsed_results = self.scraper.parse_search_results(html)
#         self.assertGreater(len(parsed_results), 0)
#         pprint.pprint(parsed_results)


class TestScrapers(BaseTest):
    pass



for name, Scraper in scrapers.all_scrapers.iteritems():
    def wrapper(name, Scraper):
        def test(self):
            scraper = Scraper()
            html = scraper.search()
            parsed_results = scraper.parse_search_results(html)
            self.assertGreater(len(parsed_results), 0)
            pprint.pprint(parsed_results)
        return test
    f = wrapper(name, Scraper)
    f.func_name = 'test_' + name
    print f.func_name
    setattr(TestScrapers, f.func_name, f)


if __name__ == '__main__':
    print 'testing....'
    unittest.main()
