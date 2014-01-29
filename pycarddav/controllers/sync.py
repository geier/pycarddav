#!/usr/bin/env python2
# coding: utf-8
# vim: set ts=4 sw=4 expandtab sts=4:
# Copyright (c) 2011-2013 Christian Geier & contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
syncs the remote database to the local db
"""

from pycarddav import carddav
from pycarddav import backend

import logging

__all__ = ['sync']


def sync(conf):
    """this should probably be seperated from the class definitions"""

    syncer = carddav.PyCardDAV(conf.account.resource,
                               user=conf.account.user,
                               passwd=conf.account.passwd,
                               write_support=conf.account.write_support,
                               verify=conf.account.verify,
                               auth=conf.account.auth)
    my_dbtool = backend.SQLiteDb(db_path=conf.sqlite.path,
                                 encoding="utf-8",
                                 errors="stricts",
                                 debug=conf.debug)
    # sync:
    abook = syncer.get_abook()  # type(abook): dict
    my_dbtool.check_account_table(conf.account.name, conf.account.resource)

    for href, etag in abook.iteritems():
        if my_dbtool.needs_update(href, conf.account.name, etag=etag):
            logging.debug("getting %s etag: %s", href, etag)
            vcard = syncer.get_vcard(href)
            my_dbtool.update(vcard, conf.account.name, href=href, etag=etag)

    remote_changed = False
    # for now local changes overwritten by remote changes
    logging.debug("looking for locally changed vcards...")

    hrefs = my_dbtool.get_changed(conf.account.name)

    for href in hrefs:
        try:
            logging.debug("trying to update %s", href)
            card = my_dbtool.get_vcard_from_db(href, conf.account.name)
            logging.debug("%s", my_dbtool.get_etag(href, conf.account.name))
            syncer.update_vcard(card.vcf, href, None)
            my_dbtool.reset_flag(href, conf.account.name)
            remote_changed = True
        except carddav.NoWriteSupport:
            logging.info('failed to upload changed card {0}, '
                         'you need to enable write support, '
                         'see the documentation', href)
    # uploading
    hrefs = my_dbtool.get_new(conf.account.name)
    for href in hrefs:
        try:
            logging.debug("trying to upload new card %s", href)
            card = my_dbtool.get_vcard_from_db(href, conf.account.name)
            (href_new, etag_new) = syncer.upload_new_card(card.vcf)
            my_dbtool.update_href(href,
                                  href_new,
                                  conf.account.name,
                                  status=backend.OK)
            remote_changed = True
        except carddav.NoWriteSupport:
            logging.info('failed to upload card %s, '
                         'you need to enable write support, '
                         'see the documentation', href)

    # deleting locally deleted cards on the server
    hrefs_etags = my_dbtool.get_marked_delete(conf.account.name)

    for href, etag in hrefs_etags:
        try:
            logging.debug('trying to delete card %s', href)
            syncer.delete_vcard(href, etag)
            my_dbtool.delete_vcard_from_db(href, conf.account.name)
            remote_changed = True
        except carddav.NoWriteSupport:
            logging.info('failed to delete card {0}, '
                         'you need to enable write support, '
                         'see the documentation'.format(href))

    # detecting remote-deleted cards
    # is there a better way to compare a list of unicode() with a list of str()
    # objects?

    if remote_changed:
        abook = syncer.get_abook()  # type (abook): dict
    r_href_account_list = my_dbtool.get_all_href_from_db_not_new(
        [conf.account.name])
    delete = set([href for href, account in r_href_account_list]).difference(abook.keys())
    for href in delete:
        my_dbtool.delete_vcard_from_db(href, conf.account.name)
