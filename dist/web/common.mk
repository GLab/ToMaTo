VERSION?=$(_VERSION)
DEBNAME=$(PACKAGE)_$(VERSION)
DIR=$(PACKAGE)-$(VERSION)
ORIG=$(DEBNAME).orig.tar.gz
DEBFILE=$(DEBNAME)_*.deb
CHANGES=debian.tar.gz

default: build

unpack: $(ORIG) $(CHANGES)
	tar -xzf $(ORIG)
	tar -xzf $(CHANGES) -C $(DIR)
	(cd $(DIR); QUILT_PATCHES=debian/patches QUILT_REFRESH_ARGS="-p ab --no-timestamps --no-index" quilt push -a; cd ..)

$(DIR): unpack

pack:
	(cd $(DIR); debuild clean; cd ..)
	dpkg-source --format="3.0 (quilt)" --compression=gzip -b $(DIR)
	mv $(DEBNAME).$(CHANGES) $(CHANGES)
	rm $(DEBNAME).dsc


build: $(DEBFILE)
$(DEBFILE): $(DIR)
	(cd $(DIR); debuild -b -us -uc; cd ..)

init: $(ORIG) create_debian pack
create_debian:
	tar -xzf $(ORIG)
	(cd $(DIR); dh_make -n ; cd ..)

clean:
	rm -rf $(DIR)
	rm -f $(DEBNAME)_*.*

release: pack clean version unpack changelog build
changelog: $(DIR)
	(cd $(DIR); dch -v $(VERSION); cd ..)	

version:
	sed -i 's/$(_VERSION)/$(VERSION)/g' Makefile
