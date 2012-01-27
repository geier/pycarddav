all: doc

VERSION := $(shell cat VERSION)

UNAME := $(shell uname)
ifeq ($(UNAME), Linux)
	 RSTHTML = rst2html
endif
ifeq ($(UNAME), FreeBSD)
	RSTHTML = rst2html.py
endif

doc: README.rst
	$(RSTHTML) --link-stylesheet --template=template.txt --stylesheet=http://pycarddav.lostpackets.de/css/main.css --no-generator README.rst > README.html

tar:
	echo "\n##################################\n make doc und danach eingecheckt?\n##################################\n"
	sleep 3
	mkdir pycarddav$(VERSION)
	cp README.rst README.html pc_query pycard.conf.sample pycardsyncer pycarddav$(VERSION)
	tar -czf pycarddav$(VERSION).tgz pycarddav$(VERSION)/*
	rm -rf pycarddav$(VERSION)

update_web: doc
	scp README.html pycarddav.lostpackets.de:pycarddav.lostpackets.de/index.html

release: tar
	scp pycarddav$(VERSION).tgz pycarddav.lostpackets.de:pycarddav.lostpackets.de/download/

clean:
	rm *.tgz

.PHONY: clean
