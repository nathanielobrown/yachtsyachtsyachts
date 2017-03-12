cd $(dirname @0)/..

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

# Start workers
WORKER_NAME=boat_search_celery_workers
docker rm -f $WORKER_NAME
docker run -d --restart always \
	--name $WORKER_NAME \
	--network ooloo \
	-e BROKER_NAME=$BROKER_NAME \
	boat_search \
	celery -A app.celery worker --loglevel=info --concurrency 8

# Start app server
APP_NAME=boat_search
docker rm -f $APP_NAME
docker run -d --restart always \
	--name $APP_NAME \
	-e BROKER_NAME=$BROKER_NAME \
	--network ooloo \
	boat_search