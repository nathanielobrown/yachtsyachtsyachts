DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..

docker build -t yyy .
docker-compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d
# docker-compose logs --follow flask
docker-compose exec flask flask run --reload  --port=80 --host=0.0.0.0