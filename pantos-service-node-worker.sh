#! /bin/sh

poetry run celery --config -A pantos.servicenode worker -l INFO -n pantos.servicenode -Q transfers,bids