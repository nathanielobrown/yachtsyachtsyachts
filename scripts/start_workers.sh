cd ..
# -A and --app do not seem interchangeable for celery 4.0.2. Bug?
celery -A app.celery worker \
	--loglevel=info \
	--concurrency 8