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
sync:
	rsync -av ../../backend/ $(PACKAGE)/ --filter 'merge files'

.PHONY: clean
clean:
	(cd $(PACKAGE); debuild clean; cd ..)
	rm -rf $(PACKAGE)_*
	rm -rf $(PACKAGE)/tomato
	rm -rf $(PACKAGE)/server.py
	rm -rf $(PACKAGE)/manage.py
	rm -rf $(PACKAGE)/backend.conf.example
