PANTOS_SERVICE_NODE_REVISION ?= 1
PANTOS_SERVICE_NODE_SSH_HOST ?= bdev-service-node

.PHONY: dist
dist: tar wheel debian

.PHONY: code
code: check format lint sort bandit test

.PHONY: check
check:
	mypy pantos/servicenode

.PHONY: sort
sort:
	isort --force-single-line-imports pantos/servicenode tests

.PHONY: bandit
bandit:
	bandit -r pantos/servicenode tests --quiet --configfile=.bandit

.PHONY: test
test:
	python3 -m pytest tests --ignore tests/database/postgres

.PHONY: test-postgres
test-postgres:
	python3 -m pytest tests/database/postgres

.PHONY: coverage
coverage:
	python3 -m pytest --cov-report term-missing --cov=pantos tests --ignore tests/database/postgres
	rm .coverage

.PHONY: lint
lint:
	flake8 pantos/servicenode tests

.PHONY: format
format:
	yapf --in-place --recursive pantos/servicenode tests

.PHONY: tar
tar: dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION).tar.gz

dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION).tar.gz: environment-variables pantos/ alembic.ini pantos-service-node.conf.$(PANTOS_SERVICE_NODE_ENVIRONMENT) pantos-service-node.sh submodules/common/pantos/common/
	mkdir -p build/tar/pantos
	mkdir -p dist
	cp pantos-service-node.conf.$(PANTOS_SERVICE_NODE_ENVIRONMENT) build/tar/pantos-service-node.conf
	cp alembic.ini build/tar/pantos/alembic.ini
	cp pantos-service-node.sh build/tar/
	chmod 755 build/tar/pantos-service-node.sh
	cp pantos/__init__.py build/tar/pantos/
	cp --recursive pantos/servicenode/ build/tar/pantos/
	cp --recursive submodules/common/pantos/common/ build/tar/pantos/
	cd build/tar/; \
		tar --exclude='__pycache__' -czvf ../../dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION).tar.gz *

.PHONY: wheel
wheel: dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl

dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl: environment-variables pantos/ alembic.ini pantos-service-node.conf.$(PANTOS_SERVICE_NODE_ENVIRONMENT) setup.py submodules/common/pantos/common/
	cp pantos-service-node.conf.$(PANTOS_SERVICE_NODE_ENVIRONMENT) pantos/pantos-service-node.conf
	cp bids.yaml pantos/bids.yaml
	cp alembic.ini pantos/alembic.ini
	python3 setup.py bdist_wheel
	rm pantos/alembic.ini
	rm pantos/pantos-service-node.conf
	rm pantos/bids.yaml

.PHONY: debian
debian: dist/pantos-service-node-$(PANTOS_SERVICE_NODE_ENVIRONMENT)_$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all.deb

dist/pantos-service-node-$(PANTOS_SERVICE_NODE_ENVIRONMENT)_$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all.deb: environment-variables linux/ dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl
	$(eval debian_package := pantos-service-node-$(PANTOS_SERVICE_NODE_ENVIRONMENT)_$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all)
	$(eval build_directory := build/debian/$(debian_package))
	mkdir -p $(build_directory)/opt/pantos/service-node
	cp dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl $(build_directory)/opt/pantos/service-node/
	mkdir -p $(build_directory)/usr/local/bin
	cp linux/pantos-service-node-server $(build_directory)/usr/local/bin/
	mkdir -p $(build_directory)/etc/systemd/system
	cp linux/pantos-service-node-server.service $(build_directory)/etc/systemd/system/
	cp linux/pantos-service-node-celery.service $(build_directory)/etc/systemd/system/
	mkdir -p $(build_directory)/DEBIAN
	cat linux/debian/control | sed -e 's/VERSION/$(PANTOS_SERVICE_NODE_VERSION)/g' > $(build_directory)/DEBIAN/control
	cat linux/debian/postinst | sed -e 's/VERSION/$(PANTOS_SERVICE_NODE_VERSION)/g' > $(build_directory)/DEBIAN/postinst
	cp linux/debian/prerm $(build_directory)/DEBIAN/prerm
	cp linux/debian/postrm $(build_directory)/DEBIAN/postrm
	chmod 755 $(build_directory)/DEBIAN/postinst
	chmod 755 $(build_directory)/DEBIAN/prerm
	chmod 755 $(build_directory)/DEBIAN/postrm
	cd build/debian/; \
		dpkg-deb --build --root-owner-group -Zgzip $(debian_package)
	mv build/debian/$(debian_package).deb dist/

.PHONY: remote-install
remote-install: environment-variables dist/pantos-service-node-$(PANTOS_SERVICE_NODE_ENVIRONMENT)_$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all.deb
	$(eval deb_file := pantos-service-node-$(PANTOS_SERVICE_NODE_ENVIRONMENT)_$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all.deb)
	scp dist/$(deb_file) $(PANTOS_SERVICE_NODE_SSH_HOST):
	ssh -t $(PANTOS_SERVICE_NODE_SSH_HOST) "\
		sudo systemctl stop pantos-service-node-celery;\
		sudo systemctl stop pantos-service-node-server;\
		sudo apt install ./$(deb_file);\
		sudo systemctl start pantos-service-node-server;\
		sudo systemctl start pantos-service-node-celery;\
		rm $(deb_file)"

.PHONY: install
install: environment-variables dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl
	python -m pip install dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl

.PHONY: uninstall
uninstall:
	python3 -m pip uninstall -y pantos-service-node

.PHONY: clean
clean:
	rm -r -f build/
	rm -r -f dist/
	rm -r -f pantos_service_node.egg-info/

.PHONY: environment-variables
environment-variables:
ifndef PANTOS_SERVICE_NODE_ENVIRONMENT
	$(error PANTOS_SERVICE_NODE_ENVIRONMENT is undefined)
endif
ifndef PANTOS_SERVICE_NODE_VERSION
	$(error PANTOS_SERVICE_NODE_VERSION is undefined)
endif
