#!/usr/bin/env python
# coding: utf-8
# vim: set ts=4 sw=4 expandtab sts=4:
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <geier@lostpackets.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Christian Geier
# ----------------------------------------------------------------------------
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
    if not path.exists(conf.sqlite__path):
        sys.exit(str(conf.sqlite__path) + " file does not exist, please sync"
                                          " with pycardsyncer first.")

    search_string = conf.cmd__search_string.decode("utf-8")

    my_dbtool = backend.SQLiteDb(conf.sqlite__path, "utf-8", "stricts", False)

    #import:
    if conf.cmd__importing:
        cards = model.cards_from_file(conf.cmd__importing)
        for card in cards:
            my_dbtool.update(card, status=backend.NEW)
        sys.exit()

    # backup:
    if conf.cmd__backup:
        with open(conf.cmd__backup, 'w') as vcf_file:
            if search_string == "":
                hreflist = my_dbtool.get_all_vref_from_db()
            else:
                hreflist = my_dbtool.search(search_string)
            for href in hreflist:
                vcard = my_dbtool.get_vcard_from_db(href)
                vcf_file.write(vcard.vcf.encode('utf-8'))
        sys.exit()

    # editing a card:
    #if conf.cmd__edit:
    #    names = my_dbtool.select_entry2(search_string)
    #    href = ui.select_entry(names)
    #    if href is None:
    #        sys.exit("Found no matching cards.")

    # mark a card for deletion
    if conf.cmd__delete:
        hrefs = my_dbtool.search(search_string)
        if len(hrefs) is 0:
            sys.exit('Found no matching cards.')
        elif len(hrefs) is 1:
            href = hrefs[0]
        else:
            pane = ui.VCardChooserPane(my_dbtool, hrefs)
            ui.start_pane(pane)
            card = pane._walker.selected_vcard
            href = card.href

        my_dbtool.mark_delete(href)
        print('vcard "%s" deleted from local db, will be deleted on ' % href +
              'the server on the next sync')
        sys.exit()

    print("searching for " + conf.cmd__search_string + "...")
    result = my_dbtool.search(search_string)
    for one in result:
        vcard = my_dbtool.get_vcard_from_db(one)
        if conf.cmd__mutt:
            lines = vcard.print_email()
        elif conf.cmd__display_all:
            lines = vcard.pretty
        else:
            lines = vcard.pretty_min
        if not lines == '':
            print(lines.encode('utf-8'))

    return 0


def sync(conf):
    """this should probably be seperated from the class definitions"""

    syncer = carddav.PyCardDAV(conf.dav__resource,
                               user=conf.dav__user,
                               passwd=conf.dav__passwd,
                               write_support=conf.write_support,
                               verify=conf.dav__verify)

    my_dbtool = backend.SQLiteDb(conf.sqlite__path, "utf-8", "stricts", conf.debug)

    # sync:
    abook = syncer.get_abook()  # type (abook): dict

    for href, etag in abook.iteritems():
        if my_dbtool.needs_update(href, etag):
            logging.debug("getting %s etag: %s", href, etag)
            vcard = syncer.get_vcard(href)
            my_dbtool.update(vcard, href, etag=etag)

    remote_changed = False
    # for now local changes overwritten by remote changes
    logging.info("looking for locally changed vcards...")
    hrefs = my_dbtool.changed

    for href in hrefs:
        logging.info("trying to update %s", href)
        card = my_dbtool.get_vcard_from_db(href)
        card_string = card.serialize()
        card_string = card_string.replace('###COMMA###', ',')
        logging.debug("%s", my_dbtool.get_etag(href))
        syncer.update_vcard(card_string, href, None)
        my_dbtool.reset_flag(href)
        remote_changed = True
    # uploading
    hrefs = my_dbtool.get_new()
    for href in hrefs:
        logging.info("trying to upload new card %s", href)
        card = my_dbtool.get_vcard_from_db(href)
        (href_new, etag_new) = syncer.upload_new_card(card.vcf)
        my_dbtool.update_href(href, href_new, status=backend.OK)
        remote_changed = True

    # deleting locally deleted cards on the server
    hrefs_etags = my_dbtool.get_marked_delete()
    for href, etag in hrefs_etags:
        logging.info('trying to delete card %s', href)
        syncer.delete_vcard(href, etag)
        my_dbtool.delete_vcard_from_db(href)
        remote_changed = True

    # detecting remote-deleted cards
    # is there a better way to compare a list of unicode() with a list of str()
    # objects?

    if remote_changed:
        abook = syncer.get_abook()  # type (abook): dict
    rlist = my_dbtool.get_all_vref_from_db()
    delete = set(rlist).difference(abook.keys())
    for href in delete:
        my_dbtool.delete_vcard_from_db(href)
