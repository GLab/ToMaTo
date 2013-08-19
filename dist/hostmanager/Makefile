PACKAGE=tomato-hostmanager
ORIG_SOURCE=../../hostmanager

.PHONY: default
default: build

.PHONY: version
version:
	(cd custom_files; dch -n; cd ..)
	
.PHONY: build
build: clean
	rsync -aL $(ORIG_SOURCE)/ $(PACKAGE)/ --filter 'merge files'
	rsync -a custom_files/ $(PACKAGE)/
	(cd $(PACKAGE); debuild -b -us -uc; cd ..)
	
.PHONY: clean
clean:
	rm -rf $(PACKAGE)
