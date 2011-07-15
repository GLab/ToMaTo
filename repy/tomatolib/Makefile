CPP = cpp
ARGS = -nostdinc -P -traditional-cpp -Ilib

build/%: src/% lib/*
	$(CPP) $(ARGS) $< $@

DEFAULT: create_dir build

create_dir:
	mkdir -p build

build: build/dhcp_server.repy build/pingable_node.repy build/switch.repy

clean:
	rm build/*
