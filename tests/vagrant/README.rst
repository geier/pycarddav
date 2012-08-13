This vagrant box file can be used for testing pycarddav. It contains davical in
version 1.0.2 on an ubuntu precise 32 bit. There have been two accounts
configured, one (hanz) comes preloaded with all current test vcards (5), the
other (lenna) is has no card in its address book.

use it like this::

    $ vagrant box add pycarddav_box http://lostpackets.de/pycarddav/vagrant/package.box
    $ vagrant init pycarddav_box
    $ vagrant up

    test (automatic tests will be added later)

    $ vagrant destroy # this should reset all changes

the usernames/passwords are the following:

* davicall admin password: XPPVDzQc
* username: hanz password: foobar url: http://localhost:8080/davical.php/hanz/addresses/
* username: lenna password: test url: http://localhost:8080//davical/caldav.php/lenna/addresses/


Vagrantfile and Vagrantfile.pkg were used to create this package (and might be
of some use later) and were therefore included.

I triey bootstrapping the box with puppet (but failed), so there might be some
puppet leftovers (but it works anyway).
