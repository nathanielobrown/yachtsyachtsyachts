docker run -d \
	--restart always \
	--hostname boat-search-broker \
	--name boat_search_broker \
	-p 5672:5672 \
	rabbitmq:3