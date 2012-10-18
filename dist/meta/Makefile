.PHONY: default
default: build

.PHONY: build
build: tomato-host-proxmox_*.deb
tomato-host-proxmox_*.deb:
	(cd tomato-host-proxmox; debuild -b -us -uc; cd ..)

.PHONY: clean
clean:
	(cd tomato-host-proxmox; debuild clean; cd ..)
	rm -rf tomato-host-proxmox_*
