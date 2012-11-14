About
=====
*pyCardDAV* is a simple to use CardDAV_ CLI client. It has built in support for
mutt's *query_command* but also works very well solo.

*pyCardDAV* consists of *pycardsyncer*, a program
for syncing your CardDAV resource into a local database and of *pc_query*, a
program for querying the local database. *pyCardDAV* is some ugly python_ code
(actually, it's not *that* bad anymore…) that holds together vobject_, lxml_,
PyCurl_ and pysqlite_.

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
if it doesn't. You can reach me by email at pycarddav (a) lostpackets (dot) de , by
jabber/XMPP at geier (a) jabber.ccc.de or via github_

.. _github: https://github.com/geier/pycarddav/

License
-------
*pyCardDAV* is released under the Expat/MIT License:

Copyright (c) 2011-2012 Christian Geier, David Soulayrol

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
