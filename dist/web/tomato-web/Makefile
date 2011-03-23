clean: ;

install:
	install -d $(DESTDIR)/usr/share/tomato
	install -d $(DESTDIR)/usr/share/tomato/web
	install -d $(DESTDIR)/etc/apache2/sites-available
	install -m 644 tomato-web.apache $(DESTDIR)/etc/apache2/sites-available/tomato-web
	rsync -r tomato $(DESTDIR)/usr/share/tomato/web/