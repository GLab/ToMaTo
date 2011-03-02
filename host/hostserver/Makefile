PACKAGE=tomato-hostserver
DEPENDENCIES=debhelper devscripts

.PHONY: default
default: build

include ../common.mk

.PHONY: download
download: ;

.PHONY: build
build: check-build-deps $(PACKAGE)_*.deb
$(PACKAGE)_*.deb:
	(cd $(PACKAGE); debuild -b -us -uc; cd ..)

.PHONY: clean
clean:
	(cd $(PACKAGE); debuild clean; cd ..)
	rm -rf $(PACKAGE)_*
