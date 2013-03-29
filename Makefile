all: README.rst

README.rst: doc/about.rst doc/usage.rst doc/license.rst
	cat doc/about.rst doc/usage.rst doc/license.rst > README.rst
