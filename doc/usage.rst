Usage
-----
*pyCardDAV* consists of three scripts, *pycardsyncr* which is used to sync the
local database with the server, *pc_query* to interact with the local database
and *pycard-import* to import email addresses from mutt.

Execute pycardsyncer to sync your addresses to the local database. You can test
pc_query with::

        % pc_query searchstring

By default *pyCardDAV* only prints the names, email addresses and telephone
numbers of contacts matching the search string, to see all vCard properties use
the "-a" option.


For usage with mutt etc., *pyCardDAV* can also print only email addresses in a
mutt friendly format (with the "-m" option). Edit your mutt configuration so
that query_command uses pc_query:

Example from .muttrc::

        set query_command="/home/username/bin/pc_query -m '%s'"

The current version features experimental write support. If you want to
test this, first make sure **you have a backup of your data** (but please don
*NOT* rely on *pc_query --backup* for this just yet), then you can put the
line::

        write_support = YesPleaseIDoHaveABackupOfMyData

in your config file (in the default section).

You can also import, delete or backup single cards (backup also works for the
whole collection, but please don't rely on it just yet). See *pc_query --help*
for how to use these and for some more options.

Import Addresses from Mutt
--------------------------
You can directly add sender addresses from mutt to *pyCardDAV*, either adding
them to existing contacts or creating a new one. If write support is enabled,
they will be uploaded on the server during the next sync.

Example from .muttrc::

        macro index,pager A "<pipe-message>pycard-import<enter>" "add sender address to pycardsyncer"

SSL
---
If you use SSL to interact with your CardDAV Server (you probably should) and
you don't have a certificate signed by a CA your OS Vendor trusts (like a
self-signed certificate or one signed by CAcert) you can set *verify* to a path
to the CA's root file (must be in pem format). If you don't want any certificate
checking set *verify* to *false* to disable *any* ssl certificate checking (this
is not recommended).

Additional Information
----------------------
For now, VCard properties that have no value are not shown.

Also, you should be able to use *pyCardDAV*'s CardDAV implementation for other
projects. See the *CardDAV* class in *pycarddav/carddav.py*.

