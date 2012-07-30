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
* IN WORK: use logging from std lib

* handle photos etc (base64 encoded)
* use ssl public cert

BUGS
====
* BUG nicknames changing breaks vcard creation
* BUG fix vcard creation from db (ORGs are broken)
* BUG vcard printed differently on import (vobject prettyPrint)
* BUG no notification from pc_query when db exists but has not been
      successfully synced yet
* BUG local deleted vcards are first GET from the server, then DELETEd on the
  server and finally detected as remote deleted and deleted again from the local
  db

TODO
====
* TODO fix that href vref h_ref mess


DONE
====
* DONE: creating the dbs
* DONE: vcard importing
* DONE: use distutils
* DONE: owncloud works
* DONE: base url not in config anymore
* DONE: detect remote-deleted vcards, remove them from local db
