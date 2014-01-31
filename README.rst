About
=====
*pyCardDAV* is a simple to use CardDAV_ CLI client. It has built in support for
mutt's *query_command* but also works very well solo.

*pyCardDAV* consists of *pycardsyncer*, a program for syncing your CardDAV
resource into a local database and of *pc_query*, a program for querying the
local database. *pyCardDAV* is some ugly python_ code (actually, it's not
*that* bad anymore…) that holds together vobject_, lxml_, requests_ and
pysqlite_.

.. _CardDAV: http://en.wikipedia.org/wiki/CardDAV
.. _python: http://python.org/
.. _vobject: http://vobject.skyhouseconsulting.com/
.. _lxml: http://lxml.de/
.. _pysqlite: http://code.google.com/p/pysqlite/
.. _requests: http://python-requests.org

Features
--------
(or rather: limitations)

- *pyCardDAV* can only use one address book resource at the moment
- *pyCardDAV* is only tested against davical, owncloud and sabredav
- *pyCardDAV* can import the sender's address directly from mutt
- *pyCardDAV* can backup and import to/from .vcf files
- *pyCardDAV* can add email addresses directly from mutt
- *pyCardDAV* only understands VCard 3.0
- *pyCardDAV* is not python 3 compatible yet

Feedback
--------
Please do provide feedback if *pyCardDAV* works for you or even more importantly
if it doesn't. You can reach me by email at pycarddav (at) lostpackets (dot) de , by
jabber/XMPP at geier (at) jabber (dot) ccc (dot) de or via github_

.. _github: https://github.com/geier/pycarddav/

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

Usage
-----
*pyCardDAV* consists of three scripts, *pycardsyncer* which is used to sync the
local database with the server, *pc_query* to interact with the local database
and *pycard-import* to import email addresses from mutt.

Execute pycardsyncer to sync your addresses to the local database. You can test
pc_query with::

        % pc_query searchstring

By default *pyCardDAV* only prints the names, email addresses and telephone
numbers of contacts matching the search string, to see all vCard properties use
the "-A" option.


For usage with mutt etc., *pyCardDAV* can also print only email addresses in a
mutt friendly format (with the "-m" option). Edit your mutt configuration so
that query_command uses pc_query:

Example from .muttrc::

        set query_command="/home/username/bin/pc_query -m '%s'"

The current version features experimental write support. If you want to
test this, first make sure **you have a backup of your data** (but please do
*NOT* rely on *pc_query --backup* for this just yet), then you can put the
line::

        write_support = YesPleaseIDoHaveABackupOfMyData

in your config file (needs to be put into each *Account* section you want to
enable write support for).

You can also import, delete or backup single cards (backup also works for the
whole collection, but please don't rely on it just yet). See *pc_query --help*
for how to use these and for some more options.

*pycarddav* can be configured to use different CardDAV accounts, see the example
config for details. An account can be specified with *-a account_name* with all
three utilies. If no account is chosen all searching and syncing actions will
use all configured accounts, while on adding cards the first configured account
will be used.

Keyring support
---------------

*pycarddav* supports keyring_, (version >=3.0). To use it, you need to add a
password to the keyring via::

    keyring set pycarddav:$account $username

where $account is the name of an account as configured in your configuration
file and $username is the corresponding username (and then have no password
configured for that account). For more details on configuring keyring have a
look at its documentation_.

.. _keyring: https://pypi.python.org/pypi/keyring
.. _documentation: https://pypi.python.org/pypi/keyring

Import Addresses from Mutt
--------------------------
You can directly add sender addresses from mutt to *pyCardDAV*, either adding
them to existing contacts or creating a new one. If write support is enabled,
they will be uploaded on the server during the next sync.

Example from .muttrc::

        macro index,pager A "<pipe-message>pycard-import<enter>" "add sender address to pycardsyncer"

SSL
---
If you use SSL to interact with your CardDAV Server (you probably should) and
you don't have a certificate signed by a CA your OS Vendor trusts (like a
self-signed certificate or one signed by CAcert) you can set *verify* to a path
to the CA's root file (must be in pem format). If you don't want any certificate
checking set *verify* to *false* to disable *any* ssl certificate checking (this
is not recommended).

Conflict Resolution
-------------------

In case of conflicting edits (local VCard changed while remote VCard also
changed), are "resolved" by pycarddav through overwriting the local VCard with
the remote one (meaning local edits are lost in this case). Syncing more
frequently can prevent this.

Additional Information
----------------------
For now, VCard properties that have no value are not shown.

Also, you should be able to use *pyCardDAV*'s CardDAV implementation for other
projects. See the *CardDAV* class in *pycarddav/carddav.py*.

In accordance with RFC 6352 all VCards that are imported or changed by pyCardDAV
will automatically get a random UID (if they haven't one already), as some
CardDAV servers, e.g. Owncloud require these.

Debian Wheezy Quickstart
------------------------

apt-get install python-requests python-vobject python-pytest python-urwid python-lxml python-pyxdg
sudo python setup.py install
mkdir -p ~/.config/pycard
chmod 700 ~/.config/pycard
cp pycard.conf.sample ~/.config/pycard/pycard.conf

License
-------
*pyCardDAV* is released under the Expat/MIT License:

Copyright (c) 2011-2013 Christian Geier and contributors

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
