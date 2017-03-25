import os
from importlib import import_module

from base_scraper import BaseScraper

files = os.listdir(os.path.dirname(__file__))
_scraper_module_names = [n.rstrip('.py') for n in files
                        if n.endswith('.py') and n != '__init__.py' and
                        n != 'base_scraper.py']

_modules = map(lambda x: import_module('.' + x, __package__),
               _scraper_module_names)


def _find_scraper(module):
    """Returns the first class that inherits from BaseScraper in a module"""
    for name, obj in module.__dict__.iteritems():
        if isinstance(obj, type) and issubclass(obj, BaseScraper):
            return name, obj
    raise Exception('Scraper not found in {!r}'.format(obj.__name__))


all_scrapers = {}
for module in _modules:
    name, Scraper = _find_scraper(module)
    all_scrapers[name] = Scraper
