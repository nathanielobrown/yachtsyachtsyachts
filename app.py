
from flask import Flask, render_template

import scrapers


app = Flask(__name__)


@app.route('/')
def home():
    num_scrapers = len(scrapers.all_scrapers)
    return render_template('home.html', num_scrapers=num_scrapers)


if __name__ == '__main__':
    app.run(debug=True)
