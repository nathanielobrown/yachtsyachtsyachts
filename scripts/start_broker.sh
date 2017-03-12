docker run -it --rm \
	--hostname boat_search_broker \
	--name boat_search_broker \
	-p 5672:5672 \
	rabbitmq:3