PACKAGE=tomato-host
DEPENDENCIES=devscripts debhelper

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
	rm -rf $(PACKAGE)_*.{deb,build,changes}
