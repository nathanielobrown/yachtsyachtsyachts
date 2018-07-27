import unittest
import os
import sys
import pprint
import lxml

import requests_cache
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "yyy"))
import scrapers


requests_cache.install_cache("tests_cached_requests", expire_after=60*60*24)

class BaseTest(unittest.TestCase):
    pass


class TestScrapers(BaseTest):
    """Groups scrapes tests. The individual tests are added dynamically"""

    pass


for name, Scraper in scrapers.all_scrapers.items():

    def wrapper(name: str, Scraper: type):
        def test(self):
            scraper = Scraper()
            html = scraper.search("contessa", "32")
            try:
                parsed_results = scraper.parse_search_results(html)
                if len(parsed_results) == 0:
                    raise
            except Exception:
                f_name = f"{self._testMethodName}.html"
                with open(f_name, "w") as f:
                    f.write(html.decode())
                url = "file:///" + os.path.abspath(f_name)
                import webbrowser
                # webbrowser.open(url)
                raise
                # import ipdb; ipdb.set_trace()
            self.assertGreater(len(parsed_results), 0)
            pprint.pprint(parsed_results)

        return test

    f = wrapper(name, Scraper)
    f.__name__ = "test_" + name
    print(f.__name__)
    setattr(TestScrapers, f.__name__, f)
del f


if __name__ == "__main__":
    print("testing....")
    unittest.main()
