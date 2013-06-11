all: README.rst

README.rst: doc/about.rst doc/usage.rst doc/license.rst doc/installation.rst
	cat doc/about.rst doc/installation.rst doc/usage.rst doc/license.rst > README.rst
