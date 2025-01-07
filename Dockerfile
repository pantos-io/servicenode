#syntax=docker/dockerfile:1.7.0-labs
# SPDX-License-Identifier: GPL-3.0-only
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

RUN python3 -m pip install 'poetry<2.0.0'

WORKDIR /app

COPY . /app

RUN make debian-build-deps

RUN make debian debian-full wheel

FROM bitnami/minideb:bookworm AS prod

RUN apt-get update

# Do not copy the configurator package
COPY --from=dev /app/dist/pantos-service-node_*.deb .

RUN ARCH=$(dpkg --print-architecture) && \
    PKGS=$(ls ./*-signed.deb 2>/dev/null || ls ./*.deb) && \
    INSTALLED_COUNT=0 && \
    for pkg in $PKGS; do \
        if [ -f "$pkg" ]; then \
            PKG_ARCH=$(dpkg-deb --field "$pkg" Architecture) && \
            if [ "$PKG_ARCH" = "all" ] || [ "$PKG_ARCH" = "$ARCH" ]; then \
                apt-get install -f -y --no-install-recommends "$pkg" && \
                INSTALLED_COUNT=$((INSTALLED_COUNT + 1)); \
            else \
                echo "Skipping $pkg due to architecture mismatch"; \
            fi; \
        fi; \
    done && \
    if [ "$INSTALLED_COUNT" -eq 0 ]; then \
        echo "Error: No packages were installed" >&2; \
        exit 1; \
    fi && \
    rm -rf *.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM prod AS servicenode

ENV APP_PORT=8080

ENTRYPOINT ["/usr/bin/pantos-service-node-server"]

FROM prod AS servicenode-celery-worker

ENTRYPOINT ["/usr/bin/pantos-service-node-celery"]
