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

### 2.1 Pre-built packages

There are two ways to install the apps using pre-built packages:

#### Debian package distribution

We provide Debian packages alongside every release, you can find them in the [releases tab](https://github.com/pantos-io/servicenode/releases). Further information on how to use the service node packages can be found [here](https://pantos.gitbook.io/technical-documentation/general/service-node).

#### Docker images

We also distribute docker images in DockerHub with each release. These are made available under the pantosio project as either [**app**](https://hub.docker.com/r/pantosio/service-node-app) or [**worker**](https://hub.docker.com/r/pantosio/service-node-worker).

### 2.2  Prerequisites

Please make sure that your environment meets the following requirements:

#### Python Version

The Pantos Service Node requires **Python 3.10**. Ensure that you have the correct Python version installed before the installation steps. You can download the latest version of Python from the official [Python website](https://www.python.org/downloads/).

#### Library Versions

The Pantos Service Node has been tested with the library versions in **requirements.py** and **setup.py**.

### 2.3  Installation Steps

#### Virtual environment

Create a virtual environment from the repository's root directory:

```bash
$ python -m venv .venv
```

Activate the virtual environment:

```bash
$ source .venv/bin/activate
```

Install the required packages:
```bash
$ python -m pip install -r requirements.txt
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

At the moment, contributing to this project is not available. 