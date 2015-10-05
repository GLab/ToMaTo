clean: ;

install:
	install -d $(DESTDIR)/var/lib/tomato
	install -d $(DESTDIR)/var/lib/tomato/files
	install -d $(DESTDIR)/var/lib/tomato/templates
	install -d $(DESTDIR)/etc/tomato
	install -m 640 hostmanager.conf.example $(DESTDIR)/etc/tomato/hostmanager.conf
	install -m 640 hostmanager.conf.example $(DESTDIR)/etc/tomato/hostmanager.conf.example
	install -d $(DESTDIR)/etc/tomato/client_certs
	install -d $(DESTDIR)/usr/share/tomato-hostmanager
	install -m 755 server.py $(DESTDIR)/usr/share/tomato-hostmanager
	install -m 755 manage.py $(DESTDIR)/usr/share/tomato-hostmanager
	rsync -r tomato $(DESTDIR)/usr/share/tomato-hostmanager/
	install -d $(DESTDIR)/var/log/tomato
	install -d $(DESTDIR)/etc/logrotate.d
	install -m 644 logrotate.conf $(DESTDIR)/etc/logrotate.d/tomato-hostmanager
	install -d $(DESTDIR)/usr/bin
	install -m 755 update-tomato-client-certs.sh $(DESTDIR)/usr/bin/update-tomato-client-certs
	install -d $(DESTDIR)/usr/sbin
	install -m 755 vznetaddbr-tomato $(DESTDIR)/usr/sbin/vznetaddbr
	install -d $(DESTDIR)/usr/share/tomato-hostmanager/contrib
	install -m 644 dummy_floppy.raw $(DESTDIR)/usr/share/tomato-hostmanager/contrib/dummy_floppy.raw
