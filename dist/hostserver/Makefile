PACKAGE=tomato-hostserver
DEPENDENCIES=debhelper devscripts

.PHONY: default
default: build

.PHONY: build
build: $(PACKAGE)_*.deb
$(PACKAGE)_*.deb:
	(cd $(PACKAGE); debuild -b -us -uc; cd ..)

.PHONY: clean
clean:
	(cd $(PACKAGE); debuild clean; cd ..)
	rm -rf $(PACKAGE)_*
