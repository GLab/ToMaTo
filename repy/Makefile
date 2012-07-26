CPP = cpp -undef -Wundef -nostdinc -P -traditional-cpp -Ilib/seattlelib -Ilib/tomatolib

build/%: src/% lib/tomatolib/* lib/seattlelib/*
	@mkdir -p `dirname $@`
	$(CPP) $< $@

lib/seattlelib/%: seattlelib/%
	@mkdir -p `dirname $@`
	echo "#ifndef `basename $@ .repy`_loaded" >$@
	echo "#define `basename $@ .repy`_loaded" >>$@
	sed -e 's/#/ #/g;s/include \(.*\)/#include <\1>/g' $< >>$@
	echo "#endif" >>$@

DEFAULT: seattlelib-convert build

seattlelib-convert: $(shell ls seattlelib/*.repy | sed 's/seattlelib\//lib\/seattlelib\//g')

build: $(shell ls src/*.repy | sed 's/src\//build\//g')

clean:
	rm -rf build
	rm -rf lib/seattlelib
