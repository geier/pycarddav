Installation
------------
You can download *pyCardDAV* either from the above download link or check it
out from git (at github). Then install *pyCardDAV* by executing *python setup.py install*.
If you feel more adventurous you can always the *develop* branch on github, which
*should* always be in a usable state. pyCardDAV is also available on pypi_ and can
be installed via pip install pycarddav or easy_install pycarddav.

Copy and edit the supplied pycard.conf.sample file (default location is
~/.config/pycard/pycard.conf). If you don't want to store the password in
clear text in the config file, *pyCardDAV* will ask for it while syncing.

Make sure you have sqlite3 (normally available by default), vobject, lxml(>2),
requests (>0.10), urwid (>0.9) pyxdg, installed. Users of python 2.6 will also
need to install argparse.

*pyCardDAV* has so far been successfully tested on recent versions of FreeBSD,
NetBSD, Debian and Ubuntu with python 2.6 and 2.7 and against davical 0.9.9.4 -
1.0.1 (later versions should be ok, too, but 0.9.9.3 and earlier don't seem
to work), owncloud and sabredav.

.. _pypi: https://pypi.python.org/pypi/pyCardDAV/
.. _git: http://github.com/geier/pycarddav/

