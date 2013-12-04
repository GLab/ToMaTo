.PHONY: default
default: build

.PHONY: build
build: tomato-updater_*.deb
tomato-updater_*.deb:
	(cd tomato-updater; debuild -b -us -uc; cd ..)

.PHONY: clean
clean:
	(cd tomato-updater; debuild clean; cd ..)
	rm -rf tomato-updater_*
