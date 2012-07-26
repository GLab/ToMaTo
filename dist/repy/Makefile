PACKAGE=tomato-repy

.PHONY: default
default: build

.PHONY: download
download: repy_orig

repy_orig:
	svn co http://seattle.cs.washington.edu/svn/seattle/branches/repy_v2/repy repy_orig

$(PACKAGE)/repy: repy_orig
	rsync -a repy_orig/ $(PACKAGE)/repy/ --exclude *test*
	rsync -a custom_files/ $(PACKAGE)/repy/

.PHONY: build
build: $(PACKAGE)_*.deb
$(PACKAGE)_*.deb: $(PACKAGE)/repy
	(cd $(PACKAGE); debuild -b -us -uc; cd ..)

.PHONY: clean
clean:
	(cd $(PACKAGE); debuild clean; cd ..)
	rm -rf $(PACKAGE)_*
	rm -rf repy_orig
	rm -rf $(PACKAGE)/repy