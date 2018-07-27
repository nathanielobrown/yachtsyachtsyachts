docker-machine create --driver amazonec2 \
	--amazonec2-region us-east-1 \
	--amazonec2-root-size 30 \
	--amazonec2-instance-type t2.micro \
	--amazonec2-open-port 80 \
	--amazonec2-open-port 443 \
	aws4