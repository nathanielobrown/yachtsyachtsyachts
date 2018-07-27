DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..

# docker build -t boat_search https://nathanielobrown@gitlab.com/nathanielobrown/boat_search.git
# docker build -t nathanielobrown/yyy .

docker-compose up -d