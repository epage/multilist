all: build_mo
	python2.5 setup.py build  
clean: 
	rm -rf ./locale ./po/templates.pot
	python2.5 setup.py clean --all
install: build_mo
	python2.5 setup.py install --root $(DESTDIR) 

TEXT_DOMAIN=multilist
POTFILES=src/multilist $(wildcard src/multilistclasses/*.py)

update_po: po/templates.pot
	@for lang in $(basename $(notdir $(wildcard po/*.po))); do \
		msgmerge -U --strict --no-wrap po/$$lang.po po/templates.pot; \
	done

po/templates.pot: $(POTFILES)
	xgettext --language=Python --strict --no-wrap --output=$@ $(POTFILES)

build_mo:
	@for lang in $(basename $(notdir $(wildcard po/*.po))); do \
		mkdir -p locale/$$lang/LC_MESSAGES; \
		msgfmt --statistics -c -o locale/$$lang/LC_MESSAGES/$(TEXT_DOMAIN).mo po/$$lang.po; \
	done

.PHONES: update_po build_mo
