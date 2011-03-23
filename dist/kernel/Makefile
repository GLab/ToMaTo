PACKAGE=pve-kernel
DEPENDENCIES=build-essential rsync debhelper libssl-dev fakeroot quilt lintian git-core
VERSION=2.6.32_2010-12-23
FILE=$(PACKAGE)-$(VERSION).tar.gz
URL=ftp://download.proxmox.com/sources/$(FILE)
MD5=956b962fe7edba00a7a3df6e2ab894b9

.PHONY: default
default: build

include ../common.mk

.PHONY: download
download: $(FILE)
$(FILE):
	wget -c "$(URL)" -O $(FILE)
	md5sum $(FILE) | awk '{exit $$1 != "$(MD5)"}'

.PHONY: build
build: check-build-deps $(PACKAGE)-*.deb
$(PACKAGE)-*.deb: $(FILE)
	tar xzf $(FILE)
	(cd $(PACKAGE)-$(VERSION); patch -p1 < ../pve-1000hz.patch; make; cd ..)
	mv $(PACKAGE)-$(VERSION)/*.deb .

.PHONY: clean
clean:
	rm -rf $(FILE) $(PACKAGE)-$(VERSION) *.deb
