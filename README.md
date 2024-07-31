<img src="https://raw.githubusercontent.com/pantos-io/servicenode/img/pantos-logo-full.svg" alt="Pantos logo" align="right" width="120" />

[![CI](https://github.com/pantos-io/servicenode/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/pantos-io/servicenode/actions/workflows/ci.yaml) 
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=pantos-io_servicenode&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=pantos-io_servicenode)



# Pantos Service Node (reference implementation)

## 1. Introduction

### 1.1 Overview

Welcome to the documentation for Pantos Service Node. 

The Pantos Service Node is responsible for initiating cross-chain transfers on behalf of the users. To initiate a cross-chain token transfer, a client has to send a signed request to a service node. To find an appropriate service node, the client can query the PantosHub contract of the source blockchain. To enable this, each service node registers itself at the PantosHub contract of each source blockchain supported by the service node.

### 1.2 Features

The Pantos Service Node is split into two applications:

#### Web server application

The web server application is responsible for the following:

1. Serving signed (by the service node) bids.
2. Accepting signed (by the user) transfer requests.

#### Celery application

The celery application is responsible for the following:

1. Updating the bids later served to the user through the web application.
2. Submitting the signed transfer requests to the source blockchain.

## 2. Installation

### IMPORTANT ###

We provide two ways to modify the app configuration, either through `service-node-config.env` or `service-node-config.yml`. We recommend using the `.env` file, as the `.conf` file is overwritten on every install.

While using the `.env` file you need to be aware that any fields containing certain special characters need to be wrapped around single quotes (e.g. `ETHEREUM_PRIVATE_KEY_PASSWORD='12$$#%R^'`).

The application will complain on startup should the configuration be incorrect.

### 2.1 Pre-built packages

There are two ways to install the apps using pre-built packages:

#### Debian package distribution

We provide Debian packages alongside every release, you can find them in the [releases tab](https://github.com/pantos-io/servicenode/releases). Further information on how to use the service node packages can be found [here](https://pantos.gitbook.io/technical-documentation/general/service-node).

We have a PPA hosted on GitHub, which can be accessed as follows:

```bash
curl -s --compressed "https://pantos-io.github.io/servicenode/KEY.gpg" | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/servicenode.gpg >/dev/null
sudo curl -s --compressed -o /etc/apt/sources.list.d/pantos-servicenode.list "https://pantos-io.github.io/servicenode/pantos-servicenode.list"
sudo apt update
sudo apt install pantos-service-node
```

#### Docker images

We also distribute docker images in DockerHub with each release. These are made available under the pantosio project as either [**app**](https://hub.docker.com/r/pantosio/service-node-app) or [**worker**](https://hub.docker.com/r/pantosio/service-node-worker).

##### Local Setup

You can run a local setup with docker by doing the following steps:

- Run `make docker` on the `ethereum-contracts` project
- The variables `DB_URL`, `CELERY_BACKEND` and `CELERY_BROKER` are already defined in the `docker-compose.yml`
- Modify the `docker.env` file to match your current setup
- Ensure you have a `signer_key` file located in the same directory. If you don't, you can create one with `make signer-key`
- Run `make docker`

##### Production Setup

The production setup is slightly different, for convenience we provide a separate `.env` file and `make` method.

- The variables `DB_URL`, `CELERY_BACKEND` and `CELERY_BROKER` are already defined in the `docker-compose.yml`
- Modify the `.env` file (**not** `docker.env`) to match your current setup
- Ensure you have a `signer_key` file located in the same directory. If you don't, you can create one with `make signer-key`
- Run `make docker-prod`

Please note that you may need to add a load balancer or another webserver in front of this setup should you want to host this setup under a specific domain.

If you're hosting this on a cloud provider (AWS, GCP, Azure or alike), these are normally provided. You just need to point the load balancer to the port exposed by the app, `8080`, and configure the rest accordingly.

#### Python package

We distribute the package in pypi under the following project and https://pypi.org/project/pantos-service-node/. You can install it to your project by using `pip install pantos-service-node`.

### 2.2 Prerequisites

Please make sure that your environment meets the following requirements:

#### Python Version

The Pantos Service Node supports **Python 3.10** or higher. Ensure that you have the correct Python version installed before the installation steps. You can download the latest version of Python from the official [Python website](https://www.python.org/downloads/).

#### Library Versions

The Pantos Service Node has been tested with the library versions specified in **poetry.lock**.

#### Poetry

Poetry is our tool of choice for dependency management and packaging.

Installing: 
https://python-poetry.org/docs/#installing-with-the-official-installer
or
https://python-poetry.org/docs/#installing-with-pipx

By default poetry creates the venv directory under under ```{cache-dir}/virtualenvs```. If you opt for creating the virtualenv inside the project’s root directory, execute the following command:
```bash
poetry config virtualenvs.in-project true
```

#### Conda (Debian package building only)

Conda is only required to build the Debian package. To install conda, follow the instructions [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html). Check the installation was correct running `conda -version`.


### 2.2  Installation Steps

#### Libraries

Create the virtual environment and install the dependencies:

```bash
poetry install --no-root
```

#### Pre-commit

In order to run pre-commit before a commit is done, you have to install it:

```bash
pre-commit install --hook-type commit-msg -f && pre-commit install
```

Whenever you try to make a commit, the pre-commit steps are executed.

## 3. Usage

### 3.1 Format, lint and test

Run the following command from the repository's root directory:

```bash
make code
```

### 3.2 Local development environment

#### PostgreSQL

Launch the PostgreSQL interactive terminal:

```bash
sudo -u postgres psql
```

Create a Service Node user and three databases:

```
CREATE ROLE "pantos-service-node" WITH LOGIN PASSWORD '<PASSWORD>';
CREATE DATABASE "pantos-service-node" WITH OWNER "pantos-service-node";
CREATE DATABASE "pantos-service-node-celery" WITH OWNER "pantos-service-node";
CREATE DATABASE "pantos-service-node-test" WITH OWNER "pantos-service-node";
```

#### RabbitMQ

Create a Service Node user and virtual host:

```
sudo rabbitmqctl add_user pantos-service-node <PASSWORD>
sudo rabbitmqctl add_vhost pantos-service-node
sudo rabbitmqctl set_permissions -p pantos-service-node pantos-service-node ".*" ".*" ".*"
```

## 4. Contributing

For contributions take a look at our [code of conduct](CODE_OF_CONDUCT.md).