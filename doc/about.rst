About
=====
*pyCardDAV* is a simple to use CardDAV_ CLI client. It has built in support for
mutt's *query_command* but also works very well solo (and with other MUAs).

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
jabber/XMPP at geier (at) jabber (dot) lostpackets (dot) de or via github_.

.. _github: https://github.com/geier/pycarddav/

