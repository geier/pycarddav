pyCardDAV v0.4 released
========================
:date: 15.11.2012
:category: News
:tags: Releases

pyCardDAV v0.4_ is released. This is a mayor rewrite (again), so some previously
fixed bugs might be back in. If your upgrading, you should delete your database
file first.

On the plus side, there are some new features in *pyCardDAV*:
 * **New** experimental write support in the backend
 * **New** import & export vCards
 * **New** import addresses directly from mutt
 * **New** speed increase in (initial) sync due to switching from pycurl to requests
 * **New** detects removed cards on server and delete them locally
 * **New** can delete cards locally and then on server

Also the license has changed to MIT/Expat, see the *COPYING* file for details
(but a beer is still appreciated).

PyCurl is not required anymore, *pyCardDAV* relies on requests_ now (which needs
to be installed).

Special thanks to David Soulayrol who made a lot of this happen.

**Attention** please make sure you have a **backup** when you enable write
support, see *Usage* for more details.


.. _v0.4: http://pycarddav.lostpackets.de/download/pycarddav0.4.tgz
.. _requests: http://docs.python-requests.org/
