PACKAGE=tomato-repy
_VERSION=0.1
_SUBVERSION=

DEPENDENCIES=subversion
URL=http://seattle.cs.washington.edu/svn/seattle/branches/repy_v2
REV=4467
SVNDIR=repy-svn

default: build

build: check-build-deps

include ../common.mk

$(ORIG): $(SVNDIR)
	mkdir -p $(DIR)
	rsync -a $(SVNDIR)/ $(DIR)
	find $(DIR) -name .svn -exec rm -rf \{\} \; 2>/dev/null; true
	tar -czf $(ORIG) $(DIR)
	rm -r $(DIR)

download: $(SVNDIR)
$(SVNDIR):
	svn co $(URL) -r $(REV) $(SVNDIR)

clean:
	rm -rf $(SVNDIR)
