all: doc


doc: README.rst
	rst2html.py --link-stylesheet --template=template.txt --stylesheet=css/bootstrap.min.css --no-generator README.rst > README.html
	sed -i 's#<strong>Attention</strong>#<span class=\"label warning\">Attention</span>#g' README.html
	sed -i 's#<strong>New</strong>#<span class=\"label success\">New</span>#g' README.html
	sed -i 's#<strong>Warning</strong>#<span class=\"label important\">Warning</span>#g' README.html


update_web: doc
	scp README.html pycarddav.lostpackets.de:pycarddav.lostpackets.de/index.html

release:
	#scp pycarddav$(VERSION).tgz pycarddav.lostpackets.de:pycarddav.lostpackets.de/download/

clean:
	rm *.tgz
	rm -rf build dist generated MANIFEST

.PHONY: clean
