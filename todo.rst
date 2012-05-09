FEATURES
========
* **WRITE SUPPORT**
 * upload (put) DONE, but needs better etag checking
 * new upload DONE
 * DELETE

* create new vcards manually
* handle more than one search string
* gnome-keychain support
* display only certain x-properties
* test against other servers (fruux)
* use logging from std lib

BUGS
====
* BUG fix vcard creation from db (ORGs are broken)
* BUG vcard printed differently on import (vobject prettyPrint)
* BUG no notification from pc_query when db exists but has not been
      successfully synced yet
* BUG type properties/all properties not properly saved ??? Really?

TODO
====
* TODO fix that href vref h_ref mess


DONE
====
* DONE: handle photos etc (base64 encoded)
* DONE: creating the dbs
* DONE: use ssl public cert
* DONE: vcard importing
* DONE: use distutils
* DONE: owncloud works
* DONE: base url not in config anymore
* DONE: detect remote-deleted vcards, remove them from local db
* DONE fixed the magic binary props multiplication
