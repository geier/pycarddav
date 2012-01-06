pyCardDAV
=========
News_ About_ Features_ Installation_ Usage_ Feedback_ Download_ License_

News
----
**08.12.2011:** pyCardDAV v0.3_ released:

this fixes an unicode bug and has a lot of internal changes

*Attention*: pc-query has been renamed to pc_query

if you are upgrading:
  make sure to delete the old database, also the config file
  format has somewhat changed

**10.10.2011:** pyCardDAV v0.2.1_ released

**14.09.2011:** pyCardDAV v0.2_ released

**13.09.2011:** pyCardDAV moved to github_, feel free to fork etc.

**12.08.2011:** pyCardDAV v0.1_ released

.. _v0.3: http://pycarddav.lostpackets.de/download/pycarddav0.3.tgz
.. _v0.2.1: http://pycarddav.lostpackets.de/download/pycarddav0.2.1.tgz
.. _v0.2: http://pycarddav.lostpackets.de/download/pycarddav0.2.tgz
.. _github: https://github.com/geier/pycarddav/
.. _v0.1: http://pycarddav.lostpackets.de/download/pycarddav01.tgz

About
-----
*pyCardDAV* is supposed to provide a simple way of accessing a CardDAV_
resource, mainly for use with mutt's query_command, but it might be of some use
solo.  *pyCardDAV* consists of *pycardsyncer*, a program for syncing your
CardDAV resource into a local database and of *pc_query*, a program for
querying the local database. *pyCardDAV* is some ugly python code that holds
together vobject_, lxml_, PyCurl_ and pysqlite_.

.. _CardDav: http://en.wikipedia.org/wiki/CardDAV
.. _vobject: http://vobject.skyhouseconsulting.com/
.. _lxml: http://lxml.de/
.. _PyCurl: http://pycurl.sourceforge.net/
.. _pysqlite: http://code.google.com/p/pysqlite/

Features
--------
(or rather: limitations)

- *pyCardDAV* can only use one addressbook resource at the moment
- *pyCardDAV* is read-only for now
- *pyCardDAV* is only tested against davical
- your password is stored in cleartext in the config file

Installation
------------
Move pc_query and pycardsyncer to some folder in your PATH.
Copy and edit the supplied pycard.conf.sample file (default location is
~/.pycard/pycard.conf). Beware that only you can access this file, if you
have untrusted users on your machine, since the password is stored in
cleartext.

Make sure you have pysqlite3, py-vobject, pycurl and py-lxml installed.
Also *pyCardDAV* currently only works with python 2.7.

Usage
-----
Execute pycardsyncer to sync your addresses to the local database (I am
doing this every 60 minutes via cronjob). You can test pc_query with::

        % pc_query searchstring

By default *pyCardDAV* only prints the names, email addresses and telephone
numbers of contacts matching the search string, to see all vCard properties use
the "-a" option.


For usage with mutt etc., *pyCardDAV* can also print only email addresses in a
mutt friendly format (with the "-m" option). Edit your mutt configuration so
that query_command uses pc_query:

Example from .muttrc::

        set query_command="/home/username/bin/pc_query -m '%s'"

*pyCardDAV* has so far been successfully tested on recent versions of FreeBSD,
Debian and Ubuntu.

Feedback
--------
Please do provide feedback if *pyCardDAV* works for you or even more importantly
if it doesn't. You can reach me by email at pycarddav@lostpackets.de , by
jabber/XMPP at geier@jabber.ccc.de or via github_

.. _github: https://github.com/geier/pycarddav/

Download
--------
Get the latest version of pyCardDAV from http://pycarddav.lostpackets.de/
or check out it out at https://github.com/geier/pycarddav .


License
-------
*pyCardDAV* is released as beer-ware

"THE BEER-WARE LICENSE" (Revision 42):
Christian Geier wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Christian Geier


