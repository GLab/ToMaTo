clean: ;

install:
	install -d $(DESTDIR)/usr/share/tomato
	install -d $(DESTDIR)/usr/share/tomato/backend
	install -d $(DESTDIR)/etc
	install -m 644 tomato.conf $(DESTDIR)/etc/tomato.conf
	install -m 755 server.py $(DESTDIR)/usr/share/tomato/backend
	rsync -r tomato $(DESTDIR)/usr/share/tomato/backend/
	install -d $(DESTDIR)/var/log/tomato