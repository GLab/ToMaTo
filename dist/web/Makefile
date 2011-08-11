PACKAGE=tomato-web
_VERSION=2.1.2

include ../common.mk

$(ORIG):
	mkdir -p tmp/$(DIR)
	rsync -a ../../web/ tmp/$(DIR) --filter 'merge files'
	(cd tmp; tar -czf ../$(ORIG) $(DIR); cd ..)
	rm -rf tmp
