NLXTP_VERSION=0.3

.PHONY: default
default: files/prepare_vm.sh

files/prepare_vm.sh: prepare_vm.sh
	cp -a prepare_vm.sh files/prepare_vm.sh

prepare_vm/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb: ../../dist/nlxtp_guest_modules/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb
	rm prepare_vm/nlxtp-guest-modules_*.deb
	cp ../../dist/nlxtp_guest_modules/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb prepare_vm/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb
	
prepare_vm.sh: prepare_vm/* prepare_vm/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb
	../makesfx.sh -d prepare_vm -e run.sh -o prepare_vm.sh

clean:
	rm prepare_vm.sh prepare_vm/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb