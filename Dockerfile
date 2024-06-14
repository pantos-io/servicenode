FROM python:3.12-bookworm AS dev

RUN apt-get update && \
    apt-get install build-essential debhelper devscripts equivs dh-virtualenv python3-venv dh-sysuser dh-exec -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install poetry

WORKDIR /app

COPY . /app

RUN make debian-build-deps

RUN make debian

FROM bitnami/minideb:bookworm AS prod

RUN apt-get update

COPY --from=dev /app/dist/*.deb .

RUN if [ -f ./*-signed.deb ]; then \
        apt-get install -y --no-install-recommends ./*-signed.deb; \
    else \
        apt-get install -y --no-install-recommends ./*.deb; \
    fi && \
    rm -rf *.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM prod AS servicenode

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "python", "-c", 'import requests; response = requests.get("http://localhost:8080/health/live"); response.raise_for_status();' ]

ENTRYPOINT bash -c 'source /opt/pantos/pantos-service-node/virtual-environment/bin/activate && \
    exec mod_wsgi-express start-server \
    /opt/pantos/pantos-service-node/wsgi.py \
    --user pantos \
    --group pantos \
    --port 8080 \
    --log-to-terminal \
    --error-log-format "%M"'

FROM prod AS servicenode-celery-worker

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "bash", "-c", 'celery inspect ping -A pantos.servicenode -d celery@\$HOSTNAME' ]

ENTRYPOINT bash -c 'source /opt/pantos/pantos-service-node/virtual-environment/bin/activate && \
    celery \
    -A pantos.servicenode \
    worker \
    --uid $(id -u pantos) \
    --gid $(id -g pantos) \
    -l INFO \
    --concurrency 4 \
    -n pantos.servicenode \
    -Q transfers,bids'
