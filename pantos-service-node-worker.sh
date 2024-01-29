#! /bin/sh

celery -A pantos.servicenode worker -l INFO -n pantos.servicenode -Q pantos.servicenode
