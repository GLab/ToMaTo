clean: ;

install:
	install -d $(DESTDIR)/var/lib/vz/hostserver
	install -d $(DESTDIR)/usr/share/tomato
	install -d $(DESTDIR)/etc
	install -m 644 hostserver.py $(DESTDIR)/usr/share/tomato/hostserver.py
	install -m 640 tomato-hostserver.conf $(DESTDIR)/etc/tomato-hostserver.conf
