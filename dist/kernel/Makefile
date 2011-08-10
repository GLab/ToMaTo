PACKAGE=pve-kernel
DEPENDENCIES=build-essential rsync debhelper libssl-dev fakeroot quilt lintian git-core unzip
VERSION=2.6.32_2011-06-17
FILE=$(PACKAGE)-$(VERSION).tar.gz
URL=ftp://download.proxmox.com/sources/$(SRCFILE)
DIR=$(PACKAGE)-$(VERSION)
MD5=466f6b20083e221ede8fef14a2e379b0

.PHONY: default
default: check-build-deps build

.PHONY: download
download: $(FILE)
$(FILE):
	wget -c "$(URL)" -O $(FILE)
	md5sum $(FILE) | awk '{exit $$1 != "$(MD5)"}'

$(DIR): $(FILE)
	tar xzf $(FILE)
	(cd $(DIR); patch -p1 < ../pve-1000hz.patch; cd ..)

.PHONY: build
build: $(PACKAGE)-*.deb
$(PACKAGE)-*.deb: $(DIR)
	(cd $(DIR); make; cd ..)
	cp $(DIR)/*.deb .

.PHONY: clean
clean:
	rm -rf $(FILE)
	rm -f *.deb
	rm -rf $(DIR)

check-build-deps-check-deps:
	@touch no-missing-deps
	@$(foreach DEP, $(DEPENDENCIES), \
	  dpkg-query -s $(DEP) 2>/dev/null | fgrep 'install ok installed' >/dev/null \
	    || (echo "Please install the following packages and re-run make: $(DEP)"; \
	        [ -f no-missing-deps ] && rm no-missing-deps); \
	)

check-build-deps-cleanup:
	@rm no-missing-deps

check-build-deps: check-build-deps-check-deps no-missing-deps check-build-deps-cleanup
