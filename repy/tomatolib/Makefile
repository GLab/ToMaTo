CPP = cpp -undef -Wundef -nostdinc -P -traditional-cpp -Ilib

build/%: src/% lib/*
	@mkdir -p `dirname $@`
	$(CPP) $< $@

DEFAULT: build

build: $(shell ls src/* | sed 's/src\//build\//g')

clean:
	rm -rf build
