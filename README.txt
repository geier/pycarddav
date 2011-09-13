



                                    pyCardDAV                                 



   1News 1About 1Features 1Installation 1Usage 2Feedback
   2Download 2License

                                       News                                   

   12.08.2011: pyCardDAV v0.1 released

                                      About                                   

   PYCARDDAV is supposed to provide a simple way of accessing a CardDAV
   resource, mainly for use with mutt's query_command, but it might be of some
   use solo.  PYCARDDAV consists of PYCARDSYNCER, a program for syncing your
   CarDAV resource into a local database and of PC-QUERY, a program for
   querying the local database. PYCARDDAV is some ugly python code that holds
   together vobject, lxml, PyCurl and pysqlite.

                                     Features                                 

   (or rather: limitations)
   - PYCARDDAV can only use one addressbook resource at the moment
   - PYCARDDAV only stores email addresses for now
   - PYCARDDAV is read-only for now
   - PYCARDDAV is only tested against davical
   - your password is stored in cleartext in the pycardsyncer file
   - the configurion is stored in pycardsyncer, so no global installation for
     now

                                   Installation                               

   Move pc-query and pycardsyncer to your ~/bin or somewhere other users on
   your machine have no access to it, since your password is stored in
   pycardsyncer file (make sure you set the access rights properly).
   Edit the configuration sections at the top of pycardsyncer and pc-query.
   Make sure you have pysqlite3, py-vobject, pycurl and py-lxml installed.

                                      Usage                                   

   Execute pycardsyncer to sync your addresses to the local database (I am
   doing this every 60 minutes via cronjob). You can test pc-query with:

       % pc-query searchstring

   Edit your mutt configuration so that query_command uses pc-query.
   Example from .muttrc:

       set query_command="/home/username/bin/pc-query '%s'"

   PYCARDDAV has so far been tested on recent versions of FreeBSD and Ubuntu.


                                    Feedback                                 

  Please do provide feedback if PYCARDDAV works for you or even more
  importantly if it doesn't. You can reach me by email at
  pycarddav@lostpackets.de or by jabber/XMPP at geier@jabber.ccc.de

                                    Download                                 

  Get the latest version of pyCardDAV from
  http://pyCardDAV.lostpackets.de/download/latest.tgz

                                    License                                  

  PYCARDDAV is released as beer-ware
  "THE BEER-WARE LICENSE" (Revision 42): Christian Geier wrote this file. As
  long as you retain this notice you can do whatever you want with this
  stuff. If we meet some day, and you think this stuff is worth it, you can
  buy me a beer in return Christian Geier

