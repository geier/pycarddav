Usage
-----
*pyCardDAV* consists of three scripts, *pycardsyncer* which is used to sync the
local database with the server, *pc_query* to interact with the local database
and *pycard-import* to import email addresses from mutt.

Execute pycardsyncer to sync your addresses to the local database. You can test
pc_query with::

        % pc_query searchstring

By default *pyCardDAV* only prints the names, email addresses and telephone
numbers of contacts matching the search string, to see all vCard properties use
the "-A" option.


For usage with mutt etc., *pyCardDAV* can also print only email addresses in a
mutt friendly format (with the "-m" option). Edit your mutt configuration so
that query_command uses pc_query:

Example from .muttrc::

        set query_command="/home/username/bin/pc_query -m %s"

The current version features experimental write support. If you want to
test this, first make sure **you have a backup of your data** (but please do
*NOT* rely on *pc_query --backup* for this just yet), then you can put the
line::

        write_support = YesPleaseIDoHaveABackupOfMyData

in your config file (needs to be put into each *Account* section you want to
enable write support for).

You can also import, delete or backup single cards (backup also works for the
whole collection, but please don't rely on it just yet). See *pc_query --help*
for how to use these and for some more options.

*pycarddav* can be configured to use different CardDAV accounts, see the example
config for details. An account can be specified with *-a account_name* with all
three utilies. If no account is chosen all searching and syncing actions will
use all configured accounts, while on adding cards the first configured account
will be used.

Keyring support
---------------

*pycarddav* supports keyring_, (version >=3.0). To use it, you need to add a
password to the keyring via::

    keyring set pycarddav:$account $username

where $account is the name of an account as configured in your configuration
file and $username is the corresponding username (and then have no password
configured for that account). For more details on configuring keyring have a
look at its documentation_.

.. _keyring: https://pypi.python.org/pypi/keyring
.. _documentation: https://pypi.python.org/pypi/keyring

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

Conflict Resolution
-------------------

In case of conflicting edits (local VCard changed while remote VCard also
changed), are "resolved" by pycarddav through overwriting the local VCard with
the remote one (meaning local edits are lost in this case). Syncing more
frequently can prevent this.

Additional Information
----------------------
For now, VCard properties that have no value are not shown.

Also, you should be able to use *pyCardDAV*'s CardDAV implementation for other
projects. See the *CardDAV* class in *pycarddav/carddav.py*.

In accordance with RFC 6352 all VCards that are imported or changed by pyCardDAV
will automatically get a random UID (if they haven't one already), as some
CardDAV servers, e.g. Owncloud require these.


