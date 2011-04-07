clean: ;

install:
	install -d $(DESTDIR)/usr/share/tomato
	install -d $(DESTDIR)/usr/share/tomato/web
	install -d $(DESTDIR)/etc/apache2/sites-available
	install -m 644 tomato-web.apache $(DESTDIR)/etc/apache2/sites-available/tomato-web
	rsync -r tomato $(DESTDIR)/usr/share/tomato/web/
	install -d $(DESTDIR)/etc/tomato
	install -m 644 localsettings.py $(DESTDIR)/etc/tomato/webfrontend.conf
	ln -s $(DESTDIR)/etc/tomato/webfrontend.conf $(DESTDIR)/usr/share/tomato/web/tomato/localsettings.py