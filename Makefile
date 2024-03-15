PANTOS_SERVICE_NODE_VERSION ?= 0.0.0
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

dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION).tar.gz: pantos/ alembic.ini service-node-config.yml service-node-config.publish.env pantos-service-node.sh submodules/common/pantos/common/
	mkdir -p build/tar/pantos
	mkdir -p dist
	cp service-node-config.yml build/tar/service-node-config.yml
	cp service-node-config.publish.env build/tar/service-node-config.env
	cp alembic.ini build/tar/pantos/alembic.ini
	cp pantos-service-node.sh build/tar/
	chmod 755 build/tar/pantos-service-node.sh
	cp pantos/__init__.py build/tar/pantos/
	cp -R pantos/servicenode/ build/tar/pantos/
	cp -R submodules/common/pantos/common/ build/tar/pantos/
	cd build/tar/; \
		tar --exclude='__pycache__' -czvf ../../dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION).tar.gz *

.PHONY: wheel
wheel: dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl

dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl: pantos/ alembic.ini service-node-config.yml service-node-config.publish.env setup.py submodules/common/pantos/common/
	cp service-node-config.yml pantos/service-node-config.yml
	cp service-node-config.publish.env pantos/service-node-config.env
	cp bids.yml pantos/bids.yml
	cp alembic.ini pantos/alembic.ini
	python3 setup.py bdist_wheel
	rm pantos/alembic.ini
	rm pantos/service-node-config.yml
	rm pantos/service-node-config.env
	rm pantos/bids.yml

.PHONY: debian
debian: dist/pantos-service-node-$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all.deb

dist/pantos-service-node-$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all.deb: linux/ dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl
	$(eval debian_package := pantos-service-node-$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all)
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
remote-install: dist/pantos-service-node-$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all.deb
	$(eval deb_file := pantos-service-node-$(PANTOS_SERVICE_NODE_VERSION)-$(PANTOS_SERVICE_NODE_REVISION)_all.deb)
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
	python -m pip install dist/pantos_service_node-$(PANTOS_SERVICE_NODE_VERSION)-py3-none-any.whl

.PHONY: uninstall
uninstall:
	python3 -m pip uninstall -y pantos-service-node

.PHONY: clean
clean:
	rm -r -f build/
	rm -r -f dist/
	rm -r -f pantos_service_node.egg-info/
