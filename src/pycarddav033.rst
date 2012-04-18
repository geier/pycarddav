pyCardDAV v0.3.3 released
=========================

:date: 27.01.2012
:category: News
:tags: Releases

pyCardDAV v0.3.3_ is now released.

**New** pyCardDAV now features sabredav/owncloud support, thanks to Davide Gerhard for
this.

It also fixes a bug where properties with no type parameters were not printed
and a database bug.

The config file has a new entry (*davserver*) which you can set to
either davical or sabredav (depending on your CardDAV server).

Plans for the Future:
The source code has been cleaned up quite a bit (nearly every line of code
has been touched) and some features have been added. Write support is nearly
finished in the backend (but will probably not be included in the next
release yet), but the frontend is still really buggy and a pain to use. If
you want to have a look, check the repository out at github and check the
branch *write_support* (but it might be broken).

.. _v0.3.3: http://pycarddav.lostpackets.de/download/pycarddav0.3.3.tgz
