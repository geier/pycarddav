About
=====
*pyCardDAV* is a simple to use CardDAV CLI client. It has built in support for
mutt's *query_command* but also works very well solo.

*pyCardDAV* consists of *pycardsyncer*, a program
for syncing your CardDAV resource into a local database and of *pc_query*, a
program for querying the local database. *pyCardDAV* is some ugly python_ code
(actually, it's not *that* bad anymore…) that holds together vobject_, lxml_,
PyCurl_ and pysqlite_.

.. _python: http://python.org/
.. _CardDav: http://en.wikipedia.org/wiki/CardDAV
.. _vobject: http://vobject.skyhouseconsulting.com/
.. _lxml: http://lxml.de/
.. _PyCurl: http://pycurl.sourceforge.net/
.. _pysqlite: http://code.google.com/p/pysqlite/

Features
--------
(or rather: limitations)

- *pyCardDAV* can only use one addressbook resource at the moment
- *pyCardDAV* is read-only for now (but write support is coming really soon™)
- *pyCardDAV* is only tested against davical and owncloud/sabredav
- **Warning** your password is stored in cleartext in the config file

Feedback
--------
Please do provide feedback if *pyCardDAV* works for you or even more importantly
if it doesn't. You can reach me by email at pycarddav (a) lostpackets (dot) de , by
jabber/XMPP at geier (a) jabber.ccc.de or via github_

.. _github: https://github.com/geier/pycarddav/

License
-------
*pyCardDAV* is released as beer-ware

"THE BEER-WARE LICENSE" (Revision 42):
Christian Geier wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Christian Geier


