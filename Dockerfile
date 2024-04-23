FROM python:3.10-bookworm AS dev

COPY requirements.txt /app/requirements.txt
COPY setup.py /app/setup.py

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

RUN make debian

FROM bitnami/minideb:bookworm AS prod

RUN apt-get update

# TODO: Remove this whenever we mount the key and keystore as volumes
COPY --from=dev /app/dist/*.deb /

RUN apt-get install -y --no-install-recommends ./*.deb && rm -f ./*.deb && apt-get clean && rm -rf /var/lib/apt/lists/*

FROM prod AS servicenode

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "python", "-c", 'import requests; response = requests.get("http://localhost:8080/health/live"); response.raise_for_status();' ]

ENTRYPOINT bash -c 'source /opt/pantos/service-node/virtual-environment/bin/activate && \
    exec mod_wsgi-express start-server \
    /opt/pantos/service-node/wsgi.py \
    --user pantos \
    --group pantos \
    --port 8080 \
    --log-to-terminal \
    --error-log-format "%M"'

FROM prod AS servicenode-celery-worker

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "bash", "-c", 'celery inspect ping -A pantos.servicenode -d celery@\$HOSTNAME' ]

ENTRYPOINT bash -c 'source /opt/pantos/service-node/virtual-environment/bin/activate && \
    celery \
    -A pantos.servicenode \
    worker \
    --uid $(id -u pantos) \
    --gid $(id -g pantos) \
    -l INFO \
    --concurrency 4 \
    -n pantos.servicenode \
    -Q pantos.servicenode'
