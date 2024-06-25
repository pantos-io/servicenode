PANTOS_SERVICE_NODE_VERSION := $(shell poetry version -s)
PANTOS_SERVICE_NODE_SSH_HOST ?= bdev-service-node
PYTHON_FILES_WITHOUT_TESTS := pantos/servicenode linux/scripts/start-web.py
PYTHON_FILES := $(PYTHON_FILES_WITHOUT_TESTS) tests

.PHONY: check-version
check-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is not set"; \
		exit 1; \
	fi
	@VERSION_FROM_POETRY=$$(poetry version -s) ; \
	if test "$$VERSION_FROM_POETRY" != "$(VERSION)"; then \
		echo "Version mismatch: expected $(VERSION), got $$VERSION_FROM_POETRY" ; \
		exit 1 ; \
	else \
		echo "Version check passed" ; \
	fi

.PHONY: dist
dist: tar wheel debian

.PHONY: code
code: check format lint sort bandit test

.PHONY: check
check:
	poetry run mypy $(PYTHON_FILES_WITHOUT_TESTS)
	poetry run mypy --explicit-package-bases tests

.PHONY: format
format:
	poetry run yapf --in-place --recursive $(PYTHON_FILES)

.PHONY: format-check
format-check:
	poetry run yapf --diff --recursive $(PYTHON_FILES)

.PHONY: lint
lint:
	poetry run flake8 $(PYTHON_FILES)

.PHONY: sort
sort:
	poetry run isort --force-single-line-imports $(PYTHON_FILES)

.PHONY: sort-check
sort-check:
	poetry run isort --force-single-line-imports $(PYTHON_FILES) --check-only

.PHONY: bandit
bandit:
	poetry run bandit -r $(PYTHON_FILES) --quiet --configfile=.bandit

.PHONY: bandit-check
bandit-check:
	poetry run bandit -r $(PYTHON_FILES) --configfile=.bandit

.PHONY: test
test:
	poetry run python3 -m pytest tests --ignore tests/database/postgres

.PHONY: test-postgres
test-postgres:
	poetry run python3 -m pytest tests/database/postgres

.PHONY: coverage
coverage:
	poetry run python3 -m pytest --cov-report term-missing --cov=pantos tests --ignore tests/database/postgres

.PHONY: coverage-postgres
coverage-postgres:
	poetry run python3 -m pytest --cov-report term-missing --cov=pantos tests/database/postgres

.PHONY: coverage-all
coverage-all:
	poetry run python3 -m pytest --cov-report term-missing --cov=pantos tests

.PHONY: tar
tar: dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION).tar.gz

dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION).tar.gz: pantos/ service-node-config.yml service-node-config.env bids.yml alembic.ini pantos-service-node.sh pantos-service-node-worker.sh
	cp service-node-config.yml pantos/service-node-config.yml
	cp service-node-config.env pantos/service-node-config.env
	cp bids.yml pantos/bids.yml
	cp alembic.ini pantos/alembic.ini
	cp pantos-service-node.sh pantos/pantos-service-node.sh
	cp pantos-service-node-worker.sh pantos/pantos-service-node-worker.sh
	chmod 755 pantos/pantos-service-node.sh
	chmod 755 pantos/pantos-service-node-worker.sh
	poetry build -f sdist
	rm pantos/service-node-config.yml
	rm pantos/service-node-config.env
	rm pantos/bids.yml
	rm pantos/alembic.ini
	rm pantos/pantos-service-node.sh
	rm pantos/pantos-service-node-worker.sh

check-poetry-plugin:
	@if poetry self show plugins | grep -q poetry-plugin-freeze; then \
		echo "poetry-plugin-freeze is already added."; \
	else \
		echo "poetry-plugin-freeze is not added. Adding now..."; \
		poetry self add poetry-plugin-freeze; \
	fi

freeze-wheel: check-poetry-plugin
	poetry freeze-wheel

.PHONY: wheel
wheel: dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl freeze-wheel

dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl: pantos/ service-node-config.yml service-node-config.env bids.yml alembic.ini
	cp service-node-config.yml pantos/service-node-config.yml
	cp service-node-config.env pantos/service-node-config.env
	cp bids.yml pantos/bids.yml
	cp alembic.ini pantos/alembic.ini
	poetry build -f wheel
	rm pantos/service-node-config.yml
	rm pantos/service-node-config.env
	rm pantos/bids.yml
	rm pantos/alembic.ini

.PHONY: debian-build-deps
debian-build-deps:
	mk-build-deps --install --tool "apt-get --no-install-recommends -y" debian/control --remove

.PHONY: debian-full
debian-full:
	mkdir -p dist
	sed 's/VERSION_PLACEHOLDER/$(PANTOS_SERVICE_NODE_VERSION)/' configurator/DEBIAN/control.template > configurator/DEBIAN/control
	dpkg-deb --build configurator dist/pantos-service-node-full_$(PANTOS_SERVICE_NODE_VERSION)_all.deb
	rm configurator/DEBIAN/control

.PHONY: debian
debian:
	$(eval debian_package := pantos-service-node_$(PANTOS_SERVICE_NODE_VERSION)_*.deb)
	dpkg-buildpackage -uc -us -g
	mkdir -p dist
	mv ../$(debian_package) dist/

debian-all: debian debian-full

.PHONY: signer-key
signer-key:
	@if ! command -v ssh-keygen &> /dev/null; then \
        echo "ssh-keygen not found. Please install OpenSSH."; \
        exit 1; \
    fi; \
	if [ -t 0 ]; then \
        read -p "Enter path for signer key (default: ./signer_key.pem): " SIGNER_KEY_FILE; \
        echo "Enter passphrase for signer key (leave empty for no passphrase):"; \
        read -s SIGNER_KEY; echo; \
    fi; \
	if [ -z "$$SIGNER_KEY_FILE" ]; then \
		SIGNER_KEY_FILE="$$(pwd)/signer_key.pem"; \
	fi; \
	if [ -z "$$SIGNER_KEY" ]; then \
		SIGNER_KEY=""; \
	fi; \
    if ssh-keygen -t ed25519 -f "$$SIGNER_KEY_FILE" -N "$$SIGNER_KEY"; then \
        echo "SSH key generated successfully at $$SIGNER_KEY_FILE"; \
    else \
        echo "Failed to generate SSH key"; \
        exit 1; \
    fi

.PHONY: remote-install
remote-install: debian-all
	$(eval deb_file := pantos-service-node*_$(PANTOS_SERVICE_NODE_VERSION)_*.deb)
	scp dist/$(deb_file) $(PANTOS_SERVICE_NODE_SSH_HOST):
ifdef DEV_PANTOS_COMMON
	scp -r $(DEV_PANTOS_COMMON) $(PANTOS_SERVICE_NODE_SSH_HOST):
	ssh -t $(PANTOS_SERVICE_NODE_SSH_HOST) "\
		sudo systemctl stop pantos-service-node-celery;\
		sudo systemctl stop pantos-service-node-server;\
		sudo apt install -y ./$(deb_file);\
		sudo rm -rf /opt/pantos/pantos-service-node/lib/python3.*/site-packages/pantos/common/;\
		sudo cp -r common/ /opt/pantos/pantos-service-node/lib/python3.*/site-packages/pantos/;\
		sudo systemctl start pantos-service-node-server;\
		sudo systemctl start pantos-service-node-celery;\
		rm -rf common;\
		rm $(deb_file)"
else
	ssh -t $(PANTOS_SERVICE_NODE_SSH_HOST) "\
		sudo systemctl stop pantos-service-node-celery;\
		sudo systemctl stop pantos-service-node-server;\
		sudo apt install -y ./$(deb_file);\
		sudo systemctl start pantos-service-node-server;\
		sudo systemctl start pantos-service-node-celery;\
		rm $(deb_file)"
endif

.PHONY: local-common
local-common:
ifndef DEV_PANTOS_COMMON
	$(error Please define DEV_PANTOS_COMMON variable)
endif
	$(eval CURRENT_COMMON := $(shell echo .venv/lib/python3.*/site-packages/pantos/common))
	@if [ -d "$(CURRENT_COMMON)" ]; then \
		rm -rf "$(CURRENT_COMMON)"; \
		ln -s "$(DEV_PANTOS_COMMON)" "$(CURRENT_COMMON)"; \
	else \
		echo "Directory $(CURRENT_COMMON) does not exist"; \
	fi

.PHONY: install
install: dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl
	poetry run python -m pip install dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl

.PHONY: uninstall
uninstall:
	poetry run python3 -m pip uninstall -y pantos-service-node

.PHONY: clean
clean:
	rm -r -f build/
	rm -r -f dist/
	rm -r -f pantos_service_node.egg-info/
