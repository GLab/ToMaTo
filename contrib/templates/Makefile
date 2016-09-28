NLXTP_VERSION=0.3.2

.PHONY: default
default: kvm/files/prepare_vm.sh

kvm/files/prepare_vm.sh: prepare_vm.sh
	cp -a prepare_vm.sh kvm/files/prepare_vm.sh

prepare_vm/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb: ../../dist/nlxtp_guest_modules/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb
	rm -f prepare_vm/nlxtp-guest-modules_*.deb
	cp ../../dist/nlxtp_guest_modules/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb prepare_vm/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb
	
prepare_vm.sh: prepare_vm/* prepare_vm/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb
	../makesfx.sh -d prepare_vm -e run.sh -o prepare_vm.sh

clean:
	rm -f prepare_vm.sh prepare_vm/nlxtp-guest-modules_$(NLXTP_VERSION)_all.deb
