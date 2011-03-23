.PHONY: check-build-deps
check-build-deps:
	@dpkg-query -s $(DEPENDENCIES) > /dev/null 2>&1 \
		|| (echo "Please install the following packages and re-run make: $(DEPENDENCIES)"; exit 1)
