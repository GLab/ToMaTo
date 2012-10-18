VERSION?=$(_VERSION)
SUBVERSION?=$(_SUBVERSION)
VER=$(VERSION)$(SUBVERSION)
DEBNAME=$(PACKAGE)_$(VER)
DIR=$(PACKAGE)-$(VER)
ORIG=$(PACKAGE)_$(VERSION).orig.tar.gz
DEBFILE=$(DEBNAME)_*.deb
CHANGES=debian.tar.gz

default: build

unpack: deb-unpack

deb-unpack: $(ORIG) $(CHANGES)
	tar -xzf $(ORIG)
	tar -xzf $(CHANGES) -C $(DIR)
	(cd $(DIR); QUILT_PATCHES=debian/patches QUILT_REFRESH_ARGS="-p ab --no-timestamps --no-index" quilt push -a; cd ..)

$(DIR): deb-unpack

pack: deb-pack

deb-pack:
	(cd $(DIR); debuild clean; cd ..)
	dpkg-source --format="3.0 (quilt)" --commit $(DIR)
	dpkg-source --format="3.0 (quilt)" --compression=gzip -b $(DIR)
	mv $(DEBNAME).$(CHANGES) $(CHANGES)
	rm $(DEBNAME).dsc


build: $(DEBFILE)

$(DEBFILE): $(DIR)
	(cd $(DIR); debuild -b -us -uc; cd ..)

init: deb-init

deb-init: $(ORIG) create_debian deb-pack

create_debian:
	tar -xzf $(ORIG)
	(cd $(DIR); dh_make -n ; cd ..)

clean: deb-clean

deb-clean:
	rm -rf $(DIR)
	rm -f $(DEBNAME)_*.*

deb-release: deb-pack deb-clean version deb-unpack dev-changelog deb-build
deb-changelog: $(DIR)
	(cd $(DIR); dch -v $(VER); cd ..)	

version:
	sed -i 's/$(_VERSION)/$(VERSION)/g' Makefile
	sed -i 's/$(_SUBVERSION)//g' Makefile

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
