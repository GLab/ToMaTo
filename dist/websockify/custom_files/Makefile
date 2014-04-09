TARGETS=rebind.so
CFLAGS += -fPIC

all: $(TARGETS)

rebind.so: rebind.o
	$(CC) $(LDFLAGS) $^ -shared -fPIC -ldl -o $@

clean:
	rm -f rebind.o rebind.so

install: rebind.so
	install -d $(DESTDIR)/usr/share/websockify
	install -m 644 websockify.py $(DESTDIR)/usr/share/websockify/websockify.py
	install -d $(DESTDIR)/usr/share/websockify/websockify
	install -m 644 websockify/__init__.py $(DESTDIR)/usr/share/websockify/websockify/__init__.py
	install -m 644 websockify/websocket.py $(DESTDIR)/usr/share/websockify/websockify/websocket.py
	install -m 644 websockify/websocketproxy.py $(DESTDIR)/usr/share/websockify/websockify/websocketproxy.py
	install -m 644 rebind.so $(DESTDIR)/usr/share/websockify
	install -d $(DESTDIR)/usr/bin
	install -m 755 run $(DESTDIR)/usr/bin/websockify
