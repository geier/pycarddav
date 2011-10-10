all: doc

VERSION := $(shell cat VERSION)
VERSION != cat VERSION

doc: README.rst
	rst2html --link-stylesheet --stylesheet=http://pycarddav.lostpackets.de/css/main.css --no-generator README.rst > README.html

tar: doc
	mkdir pycarddav$(VERSION)
	cp README.rst README.html pc-query pycard.conf.sample pycardsyncer pycarddav$(VERSION)
	tar -czf pycarddav$(VERSION).tgz pycarddav$(VERSION)/*
	rm -rf pycarddav$(VERSION)

release: tar
	scp README.html pycarddav.lostpackets.de:pycarddav.lostpackets.de/index.html
	scp pycarddav$(VERSION).tgz pycarddav.lostpackets.de:pycarddav.lostpackets.de/download/

clean:
	rm *.tgz

.PHONY: clean
