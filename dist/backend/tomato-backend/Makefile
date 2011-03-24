clean: ;

install:
	install -d $(DESTDIR)/usr/share/tomato
	install -d $(DESTDIR)/usr/share/tomato/backend
	install -d $(DESTDIR)/etc/tomato
	install -d $(DESTDIR)/var/lib/tomato
	install -m 640 tomato.conf $(DESTDIR)/etc/tomato/tomato.conf
	install -m 755 server.py $(DESTDIR)/usr/share/tomato/backend
	rsync -r tomato $(DESTDIR)/usr/share/tomato/backend/
	install -d $(DESTDIR)/var/log/tomato