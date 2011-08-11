PACKAGE=tomato-backend
_VERSION=2.1.2
_SUBVERSION=

include ../common.mk

$(ORIG):
	mkdir -p tmp/$(DIR)
	rsync -a ../../backend/ tmp/$(DIR) --filter 'merge files'
	(cd tmp; tar -czf ../$(ORIG) $(DIR); cd ..)
	rm -rf tmp
