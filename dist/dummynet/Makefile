PACKAGE=ipfw3
_VERSION=20100319
_SUBVERSION=-4

DEPENDENCIES=pve-headers-2.6.32-5-pve build-essential cdbs devscripts
SFILE=$(VERSION)-$(PACKAGE).tgz
URL=http://info.iet.unipi.it/~luigi/dummynet/$(SFILE)
MD5=3ae97871db68f40fa7351fbde03020e5

build: hint check-build-deps

include ../common.mk

$(ORIG): $(SFILE)
	tar -xzf $(SFILE)
	mv $(PACKAGE) $(DIR)
	tar -czf $(ORIG) $(DIR)
	rm -r $(DIR)

download: $(SFILE)
$(SFILE):
	wget -c "$(URL)" -O $(SFILE)
	md5sum $(SFILE) | awk '{exit $$1 != "$(MD5)"}'

hint:
	@echo "HINT: The pve-headers-* and pve-kernel-* packages can be found in kernel/. Install with dpkg -i (first kernel, then headers)."

clean:
	rm -f $(SFILE)
