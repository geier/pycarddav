#!/usr/bin/env python
# vim: set ts=4 sw=4 expandtab sts=4:
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <geier@lostpackets.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Christian Geier
# ----------------------------------------------------------------------------

"""
utility for querying the database
"""
from __future__ import print_function

try:
    from os import path
    from pycarddav import Configuration, ConfigurationParser
    from pycarddav import capture_user_interruption
    from pycarddav import backend
    from pycarddav import model
    from pycarddav import ui

    import argparse
    import sys

except ImportError as error:
    sys.stderr.write(str(error))
    sys.exit(1)


class QueryConfigurationParser(ConfigurationParser):
    """A specialized setup tool for cards query."""
    def __init__(self, desc):
        ConfigurationParser.__init__(self, desc)

        self.set_mandatory_options([(Configuration.SECTIONS.DB, 'path')])

        self._arg_parser.add_argument(
            "-a", action="store_true", dest="cmd__display_all", default=False,
            help="prints the whole card, not only name, "
            "telephone numbers and email addresses")
        self._arg_parser.add_argument(
            "-m", action="store_true", dest="cmd__mutt", default=False,
            help="only prints email addresses, in a mutt friendly format")
        self._arg_parser.add_argument(
            "-e", action="store_true", dest="cmd__edit", default=False,
            help="edit the contact file.\n"
            "NOTE: this feature is experimental and will probably corrupt "
            "your *local* database. Your remote CardDAV resource will stay "
            "untouched, as long as You don't enable write support for the "
            "syncer.")
        self._arg_parser.add_argument(
            "cmd__search_string", metavar="SEARCHSTRING", default="",
            help="the string to search for", nargs="?")
        self._arg_parser.add_argument(
            "-b", "--backup", action="store", dest="cmd__backup",
            metavar="BACKUP",  help="backup the local db to BACKUP, "
            "if a SEARCHSTRING is present, only backup cards matching it.")
        self._arg_parser.add_argument(
            "-i", "--import", metavar="FILE",
            type=argparse.FileType("r"), dest="cmd__importing",
            help="import vcard from FILE or STDIN")
        self._arg_parser.add_argument(
            "--delete", dest="cmd__delete", action="store_true",
            help="delete card matching SEARCHSTRING")


def main():
    """main function, everything starts  here"""
    capture_user_interruption()

    # Read configuration.
    parser = QueryConfigurationParser('prints contacts cards matching a search string')

    conf = parser.parse()
    if conf is None:
        sys.exit(1)

    # testing if the db exists
    if not path.exists(conf.sqlite__path):
        sys.exit(str(conf.sqlite__path) + " file does not exist, please sync with "
                "pycardsyncer first.")

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
    if conf.cmd__edit:
        names = my_dbtool.select_entry2(search_string)
        href = ui.select_entry(names)
        if href is None:
            sys.exit("Found no matching cards.")

    # print card(s)
    if conf.cmd__delete:
        names = my_dbtool.select_entry2(search_string)
        href = ui.select_entry(names)
        if href is None:
            sys.exit('Found no matching cards.')
        my_dbtool.mark_delete(href)
        print('vcard %s deleted from local db, will be deleted on ' % href + \
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

if __name__ == "__main__":
    main()
