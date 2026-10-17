LIBS=broken good
NAVY_HOME=/tmp/ccr-p7-supp-work-dggqvqok
MAKE=/tmp/ccr-p7-supp-work-dggqvqok/fake-make
.PHONY: libs fsimg broken good
libs:
	@for t in $(LIBS); do $(MAKE) -s -C $(NAVY_HOME)/libs/$$t archive; done
fsimg: broken good
	-for t in $^; do $(MAKE) -s -C $(NAVY_HOME)/$$t install; done
broken good:
	@:
