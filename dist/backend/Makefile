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
sync: $(PACKAGE)/tomato $(PACKAGE)/server.py
$(PACKAGE)/tomato:
	rsync -av ../../backend/tomato $(PACKAGE)/ --exclude=.* --exclude=*.pyc
$(PACKAGE)/server.py:
	rsync -av ../../backend/server.py $(PACKAGE)/ --exclude=.* --exclude=*.pyc

.PHONY: clean
clean:
	(cd $(PACKAGE); debuild clean; cd ..)
	rm -rf $(PACKAGE)_*
	rm -rf $(PACKAGE)/tomato
	rm -rf $(PACKAGE)/server.py