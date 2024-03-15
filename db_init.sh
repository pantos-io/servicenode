#!/bin/sh
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE "pantos-service-node" WITH LOGIN PASSWORD 'pantos';
    CREATE DATABASE "pantos-service-node" WITH OWNER "pantos-service-node";
    CREATE DATABASE "pantos-service-node-celery" WITH OWNER "pantos-service-node";
    CREATE DATABASE "pantos-service-node-test" WITH OWNER "pantos-service-node";
EOSQL
