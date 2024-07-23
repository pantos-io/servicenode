FROM python:3.12-bookworm AS dev

RUN apt-get update && \
    apt-get install build-essential debhelper devscripts \
    equivs dh-virtualenv python3-venv dh-sysuser dh-exec \
    -y --no-install-recommends

ENV PATH="/root/miniconda3/bin:${PATH}"
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"; \
    else \
        echo "Unsupported architecture: $ARCH"; \
        exit 1; \
    fi && \
    wget "$MINICONDA_URL" -O miniconda.sh && \
    mkdir /root/.conda && \
    bash miniconda.sh -b && \
    rm -f miniconda.sh

RUN python3 -m pip install poetry

WORKDIR /app

COPY . /app

RUN make debian-build-deps

RUN make debian

FROM bitnami/minideb:bookworm AS prod

RUN apt-get update

# Do not copy the configurator package
COPY --from=dev /app/dist/pantos-service-node_*.deb .

RUN if [ -f ./*-signed.deb ]; then \
        apt-get install -y --no-install-recommends ./*-signed.deb; \
    else \
        apt-get install -y --no-install-recommends ./*.deb; \
    fi && \
    rm -rf *.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM prod AS servicenode

HEALTHCHECK --interval=10s --timeout=30s --start-period=5s --retries=5 CMD [ "/usr/bin/pantos-service-node-server", "--status" ]

ENV APP_PORT 8080

ENTRYPOINT /usr/bin/pantos-service-node-server

FROM prod AS servicenode-celery-worker

HEALTHCHECK --interval=10s --timeout=30s --start-period=20s --retries=5 CMD [ "/usr/bin/pantos-service-node-celery", "--status" ]

ENTRYPOINT /usr/bin/pantos-service-node-celery
