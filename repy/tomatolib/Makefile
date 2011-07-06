REPYPP = python ../repypp.py

build/%: src/%
	(cd src; $(REPYPP) ../$< ../$@; cd ..)

DEFAULT: create_dir build

create_dir:
	mkdir -p build

build: build/dhcp_server.repy build/pingable_node.repy build/switch.repy

clean:
	rm build/*
