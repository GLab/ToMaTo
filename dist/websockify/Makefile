PACKAGE=websockify
ORIG_VERSION=0.6.0
ORIG_FILENAME=v$(ORIG_VERSION).tar.gz
ORIG_URL=https://github.com/kanaka/websockify/archive/$(ORIG_FILENAME)
ORIG_SOURCE=websockify-$(ORIG_VERSION)

.PHONY: default
default: build

.PHONY: version
version:
	(cd custom_files; dch -n; cd ..)

$(ORIG_FILENAME):
	wget $(ORIG_URL) -O $(ORIG_FILENAME)

$(ORIG_SOURCE): $(ORIG_FILENAME)
	tar -xzf $(ORIG_FILENAME)

.PHONY: build
build: clean $(ORIG_SOURCE)
	rsync -aL $(ORIG_SOURCE)/ $(PACKAGE)/ --filter 'merge files'
	rsync -a custom_files/ $(PACKAGE)/
	(cd $(PACKAGE); debuild -b -us -uc; cd ..)
	
.PHONY: clean
clean:
	rm -rf $(PACKAGE)
