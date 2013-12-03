clean: ;

install:
	install -d $(DESTDIR)/etc
	install -d $(DESTDIR)/etc/init.d
	install -d $(DESTDIR)/usr
	install -d $(DESTDIR)/usr/bin
	install -m 644 nlXTP.conf $(DESTDIR)/etc/nlXTP.conf
	install -m 755 nlXTP_mon $(DESTDIR)/usr/bin/nlXTP_mon
	install -m 755 nlXTP_daemon $(DESTDIR)/usr/bin/nlXTP_daemon
	install -m 755 initscript/nlXTP_daemon $(DESTDIR)/etc/init.d/nlXTP_daemon
