#! /bin/sh

poetry run celery -A pantos.servicenode worker -l INFO -n pantos.servicenode -Q transfers,bids