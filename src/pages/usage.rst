Usage
=====

Installation
------------
You can download *pyCardDAV* either from the above download link or check it
out at github_.  Move pc_query and pycardsyncer to some folder in your PATH.
Copy and edit the supplied pycard.conf.sample file (default location is
~/.pycard/pycard.conf). Beware that only you can access this file, if you have
untrusted users on your machine, since the password is stored in cleartext.

Make sure you have pysqlite3, py-vobject, pycurl and py-lxml installed.
Users of python versions < 2.7 will also need to install argparse.

*pyCardDAV* has so far been successfully tested on recent versions of FreeBSD,
NetBSD, Debian and Ubuntu with python 2.6 and 2.7 and against davical 0.9.9.4 -
1.1.1 (later versions should be ok, too, but 0.9.9.3 and earlier don't seem
to work) and owncloud (which uses sabredav).

NetBSD/pkgsrc users can install *pyCardDAV* via pkgsrc_, Gentoo users can
install it via the sunrise overlay.

.. _pkgsrc: http://pkgsrc.se/misc/py-carddav

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
*pyCardDAV* uses liburl for all interaction with the CardDAV server, so, by
default, it uses curl's ssl trust files. If you use SSL to interact with your
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


