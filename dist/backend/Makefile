PACKAGE=tomato-backend
DEPENDENCIES=debhelper devscripts

.PHONY: default
default: build

include ../common.mk

.PHONY: download
download: ;

.PHONY: build
build: check-build-deps sync $(PACKAGE)_*.deb
$(PACKAGE)_*.deb:
	(cd $(PACKAGE); debuild -b -us -uc; cd ..)

.PHONY: sync
sync: $(PACKAGE)/tomato $(PACKAGE)/server.py $(PACKAGE)/manage.py $(PACKAGE)/backend.conf.example
$(PACKAGE)/tomato:
	rsync -av ../../backend/tomato $(PACKAGE)/ --exclude=.* --exclude=*.pyc
$(PACKAGE)/server.py:
	cp -a ../../backend/server.py $(PACKAGE)/
$(PACKAGE)/manage.py:
	cp -a ../../backend/manage.py $(PACKAGE)/
$(PACKAGE)/backend.conf.example:
	cp -a ../../backend/backend.conf.example $(PACKAGE)/

.PHONY: clean
clean:
	(cd $(PACKAGE); debuild clean; cd ..)
	rm -rf $(PACKAGE)_*
	rm -rf $(PACKAGE)/tomato
	rm -rf $(PACKAGE)/server.py
	rm -rf $(PACKAGE)/manage.py
	rm -rf $(PACKAGE)/backend.conf.example
