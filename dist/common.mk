.PHONY: check-build-deps-check-deps
check-build-deps-check-deps:
	@touch no-missing-deps
	@$(foreach DEP, $(DEPENDENCIES), \
	  dpkg-query -s $(DEP) 2>/dev/null | fgrep 'install ok installed' >/dev/null \
	    || (echo "Please install the following packages and re-run make: $(DEP)"; \
                [ -f no-missing-deps ] && rm no-missing-deps); \
        )

.PHONY: check-build-deps
check-build-deps: check-build-deps-check-deps no-missing-deps
