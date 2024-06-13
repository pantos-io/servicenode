PANTOS_SERVICE_NODE_VERSION := $(shell poetry version -s)
PANTOS_SERVICE_NODE_SSH_HOST ?= bdev-service-node
PYTHON_FILES_WITHOUT_TESTS := pantos/servicenode linux/scripts/pantos-service-node-server
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
	mk-build-deps --install debian/control --remove

.PHONY: debian
debian:
	$(eval debian_package := pantos-service-node_$(PANTOS_SERVICE_NODE_VERSION)_all)
	dpkg-buildpackage -uc -us -g
	mkdir -p dist
	mv ../$(debian_package).deb dist/

dist/pantos-service-node_$(PANTOS_SERVICE_NODE_VERSION)_all.deb: debian
	

.PHONY: remote-install
remote-install: dist/pantos-service-node_$(PANTOS_SERVICE_NODE_VERSION)_all.deb
	$(eval deb_file := pantos-service-node_$(PANTOS_SERVICE_NODE_VERSION)_all.deb)
	scp dist/$(deb_file) $(PANTOS_SERVICE_NODE_SSH_HOST):
	ssh -t $(PANTOS_SERVICE_NODE_SSH_HOST) "\
		sudo systemctl stop pantos-service-node-celery;\
		sudo systemctl stop pantos-service-node-server;\
		sudo apt install -y ./$(deb_file);\
		sudo systemctl start pantos-service-node-server;\
		sudo systemctl start pantos-service-node-celery;\
		rm $(deb_file)"

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
