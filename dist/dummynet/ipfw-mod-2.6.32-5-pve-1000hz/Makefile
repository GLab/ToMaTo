SRC_DIR=../ipfw3

install:
	install -d $(DESTDIR)/lib/modules/$(KERNEL)/extra/ipfw
	install -m 644 $(SRC_DIR)/dummynet2/ipfw_mod.ko $(DESTDIR)/lib/modules/$(KERNEL)/extra/ipfw/ipfw_mod.ko
