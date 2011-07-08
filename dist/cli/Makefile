PACKAGE=tomato-cli
_VERSION=2.0.0
_SUBVERSION=

include ../common.mk

$(ORIG):
	mkdir -p tmp/$(DIR)
	rsync -a ../../cli/ tmp/$(DIR) --filter 'merge files'
	(cd tmp; tar -czf ../$(ORIG) $(DIR); cd ..)
	rm -rf tmp
