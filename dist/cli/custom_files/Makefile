clean: ;

install:
	install -d $(DESTDIR)/usr/share/tomato
	install -d $(DESTDIR)/usr/share/tomato/cli
	install -m 755 tomato.py $(DESTDIR)/usr/share/tomato/cli
	install -d $(DESTDIR)/usr/share/tomato/cli/lib
	install -m 644 lib/*.py $(DESTDIR)/usr/share/tomato/cli/lib
	install -d $(DESTDIR)/usr/share/tomato/cli/lib/rpc
	install -m 644 lib/rpc/*.py $(DESTDIR)/usr/share/tomato/cli/lib/rpc
	install -d $(DESTDIR)/usr/share/tomato/cli/tests
	install -d $(DESTDIR)/usr/share/tomato/cli/tests/hostmanager
	install -d $(DESTDIR)/usr/share/tomato/cli/tests/hostmanager/objects
	install -m 644 tests/hostmanager/objects/*.py $(DESTDIR)/usr/share/tomato/cli/tests/hostmanager/objects
	install -d $(DESTDIR)/usr/share/tomato/cli/tests/backend
	install -m 644 tests/backend/*.py $(DESTDIR)/usr/share/tomato/cli/tests/backend
	install -d $(DESTDIR)/usr/bin
	ln -s ../share/tomato/cli/tomato.py $(DESTDIR)/usr/bin/tomato-cli
