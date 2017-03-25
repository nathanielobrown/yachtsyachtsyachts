DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..

# docker build -t boat_search https://nathanielobrown@gitlab.com/nathanielobrown/boat_search.git
docker build -t boat_search .

# Start broker
BROKER_NAME=boat-search-broker
docker rm -f $BROKER_NAME
docker run -d \
	--restart always \
	--network ooloo \
	--hostname $BROKER_NAME \
	--name $BROKER_NAME \
	-p 5672:5672 \
	rabbitmq:3

# Start backend
BACKEND_NAME=boat-search-backend
docker rm -f $BACKEND_NAME
docker run -d \
	--restart always \
	--network ooloo \
	--hostname $BACKEND_NAME \
	--name $BACKEND_NAME \
	-p 6379:6379 \
	redis

# Start workers
WORKER_NAME=boat_search_celery_workers
docker rm -f $WORKER_NAME
docker run -d --restart always \
	--name $WORKER_NAME \
	--network ooloo \
	-e BROKER_NAME=$BROKER_NAME \
	-e BACKEND_NAME=$BACKEND_NAME \
	boat_search \
	celery -A app.celery worker --loglevel=info --concurrency 8

# Start app server
APP_NAME=boat_search
docker rm -f $APP_NAME
docker run -d --restart always \
	--name $APP_NAME \
	-e BROKER_NAME=$BROKER_NAME \
	-e BACKEND_NAME=$BACKEND_NAME \
	--network ooloo \
	boat_search \
	uwsgi --socket :80 --manage-script-name \
	--mount /=app:app --workers 4