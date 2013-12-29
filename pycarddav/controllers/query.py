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
query the local db
"""

from pycarddav import backend

from os import path

import sys

__all__ = [ 'query' ]

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

    if conf.query.importing:
        action = importing
    elif conf.query.backup:
        action = backup
    #elif conf.query.edit:
    #   action = edit
    elif conf.query.delete: # mark a card for deletion
        action = delete
    else:
        action = search

    action(my_dbtool, search_string, conf)

    return 0


def importing(my_dbtool, search_string, conf):
    from pycarddav import model
    cards = model.cards_from_file(conf.query.importing)
    for card in cards:
        my_dbtool.update(card, conf.sync.accounts[0], status=backend.NEW)

def backup(my_dbtool, search_string, conf):
    with open(conf.query.backup, 'w') as vcf_file:
        if search_string == "":
            vcards = my_dbtool.get_all_href_from_db(conf.sync.accounts)
        else:
            vcards = my_dbtool.search(search_string, conf.sync.accounts,
                    conf.query.where)
        for vcard in vcards:
            vcf_file.write(vcard.vcf.encode('utf-8'))

def edit(my_dbtool, search_string, conf):
    from pycarddav import ui
    names = my_dbtool.select_entry2(search_string)
    href = ui.select_entry(names)
    if href is None:
        sys.exit("Found no matching cards.")

def delete(my_dbtool, search_string, conf):
    vcards = my_dbtool.search(search_string, conf.sync.accounts,
            conf.query.where)
    if len(vcards) is 0:
        sys.exit('Found no matching cards.')
    elif len(vcards) is 1:
        card = vcards[0]
    else:
        from pycarddav import ui
        href_account_list = [(c.href, c.account) for c in vcards]
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

def search(my_dbtool, search_string, conf):
    print("searching for " + conf.query.search_string + "...")

    for vcard in my_dbtool.search(search_string, conf.sync.accounts,
            conf.query.where):
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

