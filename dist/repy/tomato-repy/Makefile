clean: ;

install:
	install -d $(DESTDIR)/usr/share/pyshared/tomato-repy
	rsync -a repy/ $(DESTDIR)/usr/share/pyshared/tomato-repy/ --exclude *tests*
	install -d $(DESTDIR)/usr/bin
	ln -s /usr/share/pyshared/tomato-repy/tomato_repy.py $(DESTDIR)/usr/bin/tomato-repy
	install -m 755 repy-check $(DESTDIR)/usr/bin/repy-check
