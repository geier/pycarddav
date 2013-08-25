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

from pycarddav import backend
from pycarddav import carddav
from pycarddav import model
from pycarddav import ui

from os import path

import logging
import sys


def query(conf):
    # testing if the db exists
    if not path.exists(path.expanduser(conf.sqlite.path)):
        sys.exit(str(conf.sqlite.path) + " file does not exist, please sync"
                 " with pycardsyncer first.")

    search_string = conf.query.search_string.decode("utf-8")

    my_dbtool = backend.SQLiteDb(db_path=path.expanduser(conf.sqlite.path),
                                 encoding="utf-8",
                                 errors="stricts",
                                 debug=False)

    #import:
    if conf.query.importing:
        cards = model.cards_from_file(conf.query.importing)
        for card in cards:
            my_dbtool.update(card, conf.sync.accounts[0], status=backend.NEW)
        sys.exit()

    # backup:
    if conf.query.backup:
        with open(conf.query.backup, 'w') as vcf_file:
            if search_string == "":
                href_account_list = my_dbtool.get_all_href_from_db(
                    conf.sync.accounts)
            else:
                href_account_list = my_dbtool.search(search_string,
                                                     conf.sync.accounts)
            for href, account in href_account_list:
                vcard = my_dbtool.get_vcard_from_db(href, account)
                vcf_file.write(vcard.vcf.encode('utf-8'))
        sys.exit()

    # editing a card:
    #if conf.query.edit:
    #    names = my_dbtool.select_entry2(search_string)
    #    href = ui.select_entry(names)
    #    if href is None:
    #        sys.exit("Found no matching cards.")

    # mark a card for deletion
    if conf.query.delete:
        href_account_list = my_dbtool.search(search_string,
                                             conf.sync.accounts)
        if len(href_account_list) is 0:
            sys.exit('Found no matching cards.')
        elif len(href_account_list) is 1:
            href, account = href_account_list[0]
            card = my_dbtool.get_vcard_from_db(href, account)
        else:
            pane = ui.VCardChooserPane(my_dbtool,
                                       href_account_list=href_account_list)
            ui.start_pane(pane)
            card = pane._walker.selected_vcard
        if card.href in my_dbtool.get_new(card.account):
            # cards not yet on the server get deleted directly, otherwise we
            # will try to delete them on the server later (where they don't
            # exist) and this will raise an exception
            my_dbtool.delete_vcard_from_db(card.href, card.account)
        else:
            my_dbtool.mark_delete(card.href, card.account)
            print(u'vcard {0} - "{1}" deleted from local db, '
                  'will be deleted on the server on the next '
                  'sync'.format(card.href, card.fname))
        sys.exit()

    print("searching for " + conf.query.search_string + "...")

    result = my_dbtool.search(search_string, conf.sync.accounts)
    for href, account in result:
        vcard = my_dbtool.get_vcard_from_db(href, account)
        if conf.query.mutt_format:
            lines = vcard.print_email()
        elif conf.query.tel:
            lines = vcard.print_tel()
        elif conf.query.display_all:
            lines = vcard.pretty
        else:
            lines = vcard.pretty_min
        if not lines == '':
            print(lines.encode('utf-8'))

    return 0


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
