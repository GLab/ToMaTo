clean: ;

install:
	install -d $(DESTDIR)/usr/share/tomato-hostmanager
	install -d $(DESTDIR)/etc/tomato
	install -d $(DESTDIR)/var/lib/tomato
	install -m 640 hostmanager.conf.example $(DESTDIR)/etc/tomato/hostmanager.conf
	install -m 640 hostmanager.conf.example $(DESTDIR)/etc/tomato/hostmanager.conf.example
	install -m 755 server.py $(DESTDIR)/usr/share/tomato-hostmanager
	install -m 755 manage.py $(DESTDIR)/usr/share/tomato-hostmanager
	rsync -r tomato $(DESTDIR)/usr/share/tomato-hostmanager/
	install -d $(DESTDIR)/var/log/tomato
