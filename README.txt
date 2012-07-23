pyCardDAV
=========

News
----
27.01.2012: pyCardDAV v0.3.3_ released:
  **New** sabredav/owncloud support, thanks Davide Gerhard.

  Fixes a bug where properties with no type parameters were not printed.

  This release also fixes a small database bug.

  The config file has a new entry (*davserver*) which you can set to
  either davical or sabredav (depending on your CardDAV server).

  Future:
  The source code has been cleaned up quite a bit (nearly every line of code
  has been touched) and some features have been added. Write support is nearly
  finished in the backend (but will probably not be included in the next
  release yet), but the frontend is still really buggy and a pain to use. If
  you want to have a look, check the repository out at github and check the
  branch *write_support* (but it might me broken).

06.01.2012: pyCardDAV v0.3.2_ released:
  this is a minor bugfix update, db deleting should not be necessary. If
  everything is working fine at the moment, there is no need to upgrade.

06.01.2012: pyCardDAV v0.3.1_ released:
  this bugfix release fixes some bugs on Debian and a formatting bug (thanks to
  Antoine Sirinelli) and one more unicode bug (thanks to Thomas Klausner). Also,
  some more meaningful error messages were added.

  **Attention** if you are upgrading:
  you should delete the old database again and resync using pycardsyncer

08.12.2011: pyCardDAV v0.3_ released:
  this fixes an unicode bug and has a lot of internal changes

  **Attention** pc-query has been renamed to pc_query,
  make sure to delete the old database, also the config file
  format has somewhat changed

10.10.2011: pyCardDAV v0.2.1_ released
  this fixes a minor bug in the example config file

14.09.2011: pyCardDAV v0.2_ released
  **New** config files are now supported

13.09.2011: pyCardDAV moved to github_
  feel free to fork etc.

12.08.2011: pyCardDAV v0.1_ released
  first public version

.. _v0.3.3: http://pycarddav.lostpackets.de/download/pycarddav0.3.3.tgz
.. _v0.3.2: http://pycarddav.lostpackets.de/download/pycarddav0.3.2.tgz
.. _v0.3.1: http://pycarddav.lostpackets.de/download/pycarddav0.3.1.tgz
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
querying the local database. *pyCardDAV* is some ugly python code (it's not
*that* bad anymore) that holds
together vobject_, lxml_, requests_ and pysqlite_.

.. _CardDav: http://en.wikipedia.org/wiki/CardDAV
.. _vobject: http://vobject.skyhouseconsulting.com/
.. _lxml: http://lxml.de/
.. _pysqlite: http://code.google.com/p/pysqlite/
.. _requests: http://python-requests.org

Features
--------
(or rather: limitations)

- *pyCardDAV* can only use one addressbook resource at the moment
- *pyCardDAV* is only tested against davical and owncloud/sabredav
- *pyCardDAV* features a rudimentary vcard editor and can upload changed/deleted
  new cards on the server
- **Warning** your password is stored in cleartext in the config file

Installation
------------
You can download *pyCardDAV* either from the above download link or check it
out at github_.  Move pc_query and pycardsyncer to some folder in your PATH.
Copy and edit the supplied pycard.conf.sample file (default location is
~/.pycard/pycard.conf). Beware that only you can access this file, if you have
untrusted users on your machine, since the password is stored in cleartext.

Make sure you have pysqlite3, py-vobject, py-lxml, requests ( >
v.0.10 ) installed.  Users of python 2.6 will also need to install argparse.

*pyCardDAV* has so far been successfully tested on recent versions of FreeBSD,
NetBSD, Debian and Ubuntu with python 2.6 and 2.7 and against davical 0.9.9.4 -
1.0.1 (later versions should be ok, too, but 0.9.9.3 and earlier don't seem
to work) and owncloud (which uses sabredav).

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

The current version features some experimental write support. If you want to
test this, first make sure **you have a backup of your data**, then you can put
the line::

        write_support = YesPleaseIDoHaveABackupOfMyData

in your config file.

SSL
---
*NOT WORKING ATM*
If you use SSL to interact with your
CardDAV Server (you probably should) and you don't have a certificate signed by
a CA your OS Vendor trusts (like a self-signed certificate or one signed by
CAcert) you can set *cacert_file* to a path to the CA's root file (must be in
pem format). If you really don't care about security (you should) you can also
set *insecure_ssl* to *1* to disable *any* ssl certificate checking.

Additional Information
----------------------
For now, VCard properties that have no value are not shown.


Feedback
--------
Please do provide feedback if *pyCardDAV* works for you or even more importantly
if it doesn't. You can reach me by email at pycarddav@lostpackets.de , by
jabber/XMPP at geier@jabber.ccc.de or via github_

.. _github: https://github.com/geier/pycarddav/

License
-------
*pyCardDAV* is released as beer-ware

"THE BEER-WARE LICENSE" (Revision 42):
Christian Geier wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Christian Geier


