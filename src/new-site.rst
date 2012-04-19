Status Update Spring 2012
=========================

:date: 19.04.2012
:category: News

Write support is still not finished, some other tasks used up most of my time
(mostly work). But while it's not finished yet, editing and uploading cards is
working pretty well for me at the moment. So, in case someone wants to test
write support, I have set up a new branch called
*beta* into which I will pull versions that have no (major) known bugs. You
can check out this branch as follows:

        git clone -b beta https://github.com/geier/pycarddav.git

If you stumble upon any bugs not mentioned in *todo.rst*, please let me now.
Please **backup your data BEFORE** testing any of this!

But while I didn't finish write support, I created a new website for
*pyCardDAV*, with the help of pelican_ and bootstrap_. The new
site features an `atom feed` for all news regarding *pyCardDAV* and one that
only informs about `new releases`.

Also pycarddav's `URL has changed` (but the old download links will
continue to work). SSL_ is now available, too. 

.. _`atom feed`: https://lostpackets.de/pycarddav/feeds/all.atom.xml
.. _`new releases`: https://lostpackets.de/pycarddav/feeds/Releases.atom.xml

.. _`URL has changed`: htpp://lostpackets.de/pycarddav.
.. _SSL: https://lostpackets.de/pycarddav/

.. _pelican: http://pelican.notmyidea.org/
.. _bootstrap: twitter.github.com/bootstrap/
