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

# Start database
DATABASE_NAME=postgres
DB_CONN_STR="postgresql+psycopg2://postgres@$DATABASE_NAME:5432"
docker rm -f $DATABASE_NAME
docker run -d \
	--restart always \
	--network ooloo \
	--hostname $DATABASE_NAME \
	--name $DATABASE_NAME \
	--expose 5432 \
	--volume boat_search_postgres_data:/var/lib/postgresql/data \
	postgres:9.5

# Start workers
WORKER_NAME=boat-search-celery-workers
docker rm -f $WORKER_NAME
docker run -d --restart always \
	--name $WORKER_NAME \
	--network ooloo \
	--hostname $WORKER_NAME \
	-e BROKER_NAME=$BROKER_NAME \
	-e BACKEND_NAME=$BACKEND_NAME \
	-e DB_CONN_STR=$DB_CONN_STR \
	boat_search \
	celery -A app.celery worker --loglevel=info \
		-P eventlet \
		--max-memory-per-child 40000 \
		--concurrency 20

# Start app server
APP_NAME=boat-search
docker rm -f $APP_NAME
docker run -d --restart always \
	--name $APP_NAME \
	-e BROKER_NAME=$BROKER_NAME \
	-e BACKEND_NAME=$BACKEND_NAME \
	-e DB_CONN_STR=$DB_CONN_STR \
	--network ooloo \
	--hostname $APP_NAME \
	boat_search \
	uwsgi --socket :80 --manage-script-name \
	--mount /=app:app --workers 2 --threads 4