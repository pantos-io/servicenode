#syntax=docker/dockerfile:1.7.0-labs
# SPDX-License-Identifier: GPL-3.0-only
FROM python:3.12-bookworm AS dev

# Create a system group named "user" with the -r flag
RUN groupadd -r pantos

# Create a system user named "user" and add it to the "user" group with the -r and -g flags
RUN useradd -r -g pantos pantos

WORKDIR /app

# Change the ownership of the working directory to the non-root user "user"
RUN chown -R pantos:pantos /app

COPY . /app

# Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=2.0.0

RUN apt-get update && \
    apt-get install curl && \
    python3 -m pip install 'poetry<2.0.0' && \
    apt-get clean && \
    poetry install && \
    mkdir /var/log/pantos && \
    chown -R pantos:pantos /var/log/pantos

# Switch to the non-root user "pantos"
USER pantos
 
FROM dev AS servicenode

ENV APP_PORT=8080

ENTRYPOINT ["/app/pantos-service-node.sh"]

FROM dev AS servicenode-celery-worker

ENTRYPOINT ["/app/pantos-service-node-worker.sh"]
