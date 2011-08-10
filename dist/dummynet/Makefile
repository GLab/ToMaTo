PACKAGE=ipfw3
VERSION=20100319
SUBVERSION=-5
VER=$(VERSION)$(SUBVERSION)
DEBNAME=$(PACKAGE)_$(VER)
DEBFILE=$(DEBNAME)_*.deb
DEPENDENCIES=build-essential cdbs devscripts
SFILE=$(VERSION)-$(PACKAGE).tgz
DIR=ipfw3
KERNEL=$(shell uname -r)
MOD_DIR=ipfw-mod-$(KERNEL)
TOOLS_DIR=dummynet
URL=http://info.iet.unipi.it/~luigi/dummynet/$(SFILE)
MD5=3ae97871db68f40fa7351fbde03020e5

default: build

build: hint check-build-deps

hint:
	@echo "HINT: The pve-headers-* and pve-kernel-* packages can be found in kernel/. Install with dpkg -i (first kernel, then headers)."

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

download: $(SFILE)
$(SFILE):
	wget -c "$(URL)" -O $(SFILE)
	md5sum $(SFILE) | awk '{exit $$1 != "$(MD5)"}'

$(DIR):
	tar -xzvf $(SFILE)

build: build-mod built-tools

compile: $(DIR)
	(cd $(DIR); make; cd ..)

build-mod: compile
	(cd $(MOD_DIR); debuild -b -us -uc; cd ..)

build-tools: compile
	(cd $(TOOLS_DIR); debuild -b -us -uc; cd ..)

clean:
	rm -f $(SFILE)	
	(cd $(MOD_DIR); debuild clean; cd ..)
	(cd $(TOOLS_DIR); debuild clean; cd ..)
