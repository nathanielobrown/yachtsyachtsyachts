import datetime
import os

import dataset

import scrapers


def main():
    db_path = 'search.db'
    os.remove(db_path)
    db = dataset.connect('sqlite:///' + db_path)
    searches = db['searches']
    for name, Scraper in scrapers.all_scrapers.iteritems():
        print 'Scraping {}...'.format(name)
        scraper = Scraper()
        results = scraper.search_and_parse()
        for result in results:
            result['timestamp'] = datetime.datetime.now()
            result['scraper'] = '{} {}'.format(name, scrapers.__version__)
            searches.insert(result)
    # Save to CSV
    print 'Saving to CSV...'
    file_name = datetime.datetime.now().strftime('search_%Y_%m_%d.csv')
    dataset.freeze(searches.all(), format='csv', filename=file_name)


if __name__ == '__main__':
    main()
