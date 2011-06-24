PACKAGE=tomato-backend
_VERSION=1.4.1
_SUBVERSION=-r1

include common.mk

$(ORIG):
	mkdir -p tmp/$(DIR)
	rsync -a ../../backend/ tmp/$(DIR) --filter 'merge files'
	(cd tmp; tar -czf ../$(ORIG) $(DIR); cd ..)
	rm -rf tmp
