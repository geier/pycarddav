pyCardDAV v0.5.0 released
==========================
:date: 15.06.2013
:category: News
:tags: Releases


**New** This release brings support for multiple CardDAV accounts. See the usage
instructions, the supplied example config and/or pc_query --help. Also support
for more CardDAV servers is included. If you are upgrading, you need to delete
the local database, otherwise pyCardDAV will refuse to work. 

**Attention** In accordance with RFC 6352 all VCards that are imported
or changed by pyCadDAV will automatically get a random UID (if they
haven't one already), as some CardDAV servers, e.g. Owncloud require
these.

Download_ pyCardDAV v0.5.0, you can also install it via *pip* or *easy_install* from pypi_.

.. _Download: http://lostpackets.de/pycarddav/downloads/pyCardDAV-0.5.0.tar.gz
.. _pypi: https://pypi.python.org/pypi/pyCardDAV/
