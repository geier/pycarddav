all: doc

VERSION := $(shell cat VERSION)
VERSION != cat VERSION

doc: README.rst
	rst2html --link-stylesheet --stylesheet=http://pycarddav.lostpackets.de/css/main.css --no-generator README.rst > README.html

tar: doc
	mkdir pycarddav
	cp README.rst README.html pc-query pycard.conf.sample pycardsyncer pycarddav
	tar -cvzf pycarddav.tgz pycarddav/*
	rm pycarddav/*
	rmdir pycarddav

release: tar
	scp README.html pycarddav.lostpackets.de:pycarddav.lostpackets.de/index.html
	scp pycarddav.tgz pycarddav.lostpackets.de:pycarddav.lostpackets.de/download/pycarddav$(VERSION).tgz

clean:
	rm *.tgz

.PHONY: clean
