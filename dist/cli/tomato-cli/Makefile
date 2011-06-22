clean: ;

install:
	install -d $(DESTDIR)/usr/share/tomato
	install -d $(DESTDIR)/usr/share/tomato/cli
	install -m 755 tomato.py $(DESTDIR)/usr/share/tomato/cli
	install -d $(DESTDIR)/usr/bin
	ln -s ../share/tomato/cli/tomato.py $(DESTDIR)/usr/bin/tomato-cli
