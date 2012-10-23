PACKAGE=tomato-hostmanager
_VERSION=0.0.4
_SUBVERSION=

include ../common.mk

$(ORIG):
	mkdir -p tmp/$(DIR)
	rsync -aL ../../hostmanager/ tmp/$(DIR) --filter 'merge files'
	(cd tmp; tar -czf ../$(ORIG) $(DIR); cd ..)
	rm -rf tmp
