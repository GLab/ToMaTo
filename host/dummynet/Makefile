PACKAGE=ipfw3
DEPENDENCIES=pve-headers-2.6.32-4-pve build-essential cdbs devscripts
VERSION=20100319
FILE=$(VERSION)-$(PACKAGE).tgz
URL=http://info.iet.unipi.it/~luigi/dummynet/$(FILE)
MD5=3ae97871db68f40fa7351fbde03020e5

.PHONY: default
default: build

include ../common.mk

.PHONY: download
download: $(FILE)
$(FILE):
	wget -c "$(URL)" -O $(FILE)
	md5sum $(FILE) | awk '{exit $$1 != "$(MD5)"}'

.PHONY: hint
hint:
	@echo "HINT: The pve-headers-* and pve-kernel-* packages can be found in kernel/. Install with dpkg -i (first kernel, then headers)."

.PHONY: build
build: hint check-build-deps $(PACKAGE)-*.deb
$(PACKAGE)-*.deb: $(FILE)
	tar xzf $(FILE)
	(cd $(PACKAGE); patch -p1 < ../debian.patch; debuild -b -us -uc; cd ..)

.PHONY: clean
clean:
	rm -rf $(FILE) $(PACKAGE) $(PACKAGE)_$(VERSION)-*.{build,changes} $(PACKAGE)_*.deb
