docker run -d \
	--restart always \
	--hostname boat-search-broker \
	--name boat_search_broker \
	--expose 5672 \
	--network ooloo \
	rabbitmq:3


docker run -d \
	--restart always \
	--hostname boat-search-backend \
	--name boat-search-backend \
	--expose 6379 \
	--network ooloo \
	rabbitmq:3