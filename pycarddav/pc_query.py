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
    import sys
    import signal
    from os import path
    import argparse
    from ConfigParser import SafeConfigParser
    import pycard
    import __init__
except ImportError as error:
    print(error)
    sys.exit(1)


def signal_handler(signal, frame):
    """
    tries to hide some ugly python backtraces from the user after
    pressing ctrl-c
    """
    sys.exit(0)


def parser():
    """config and command line option parser"""
    carg_parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False
            )
    carg_parser.add_argument('-c', '--config',
            action='store', dest='configfile',
            default='~/.pycard/pycard.conf', metavar='FILE',
            help='defaults to ~/.pycard/pycard.conf')
    args, remaining_argv = carg_parser.parse_known_args()

    config_parser = SafeConfigParser(vars(args))
    config_parser.read([path.expanduser(args.configfile)])
    defaults = dict(config_parser.items('default'))

    arg_parser = argparse.ArgumentParser(
        description='prints contacts cards matching a search string')
    arg_parser.set_defaults(**defaults)
    arg_parser.add_argument("-v", "--version", action="version",
            version=__init__.__version__)
    arg_parser.add_argument(
        "-c", "--config", action="store", dest="configfile",
        default="~/.pycard/pycard.conf",
        help="defaults to ~/.pycard/pycard.conf")
    arg_parser.add_argument("-a", action="store_true", dest="display_all",
            default=False, help="prints the whole card, not only name, "
            "telephone numbers and email addresses")
    arg_parser.add_argument("-m", dest="mutt", action="store_true",
            default=False,
            help="only prints email addresses, in a mutt friendly format")
    arg_parser.add_argument("-e", dest="edit", action="store_true",
            default="False", help="edit the contact file.\n"
            "NOTE: this feature is experimental and will probably corrupt "
            "your *local* database. Your remote CardDAV resource will stay "
            "untouched, as long as You don't enable write support for the "
            "syncer.")
    arg_parser.add_argument("--debug", action="store_true", dest="debug",
            default="False", help="enable debugging")
    arg_parser.add_argument("search_string", metavar="SEARCHSTRING",
            help="the string to search for", nargs='?', default="")
    arg_parser.add_argument("-b", "--backup", action="store",
            dest="backup", help="backup the local db to BACKUP, "
            "if a SEARCHSTRING is present, only backup cards matching it.")
    arg_parser.add_argument('-i', '--import', type=argparse.FileType('r'),
            dest='importing', help='import vcard from file or STDIN')
    arg_parser.add_argument('--delete', dest='delete', action='store_true',
            help='delete card matching SEARCHSTRING')

    args = vars(arg_parser.parse_args(remaining_argv))
    return args


def main():
    """main function, everything starts  here"""
    args = parser()

    # let's try to hide some ugly python code, at least when hitting Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)

    db_path = path.expanduser(args['db_path'])
    # testing if the db exists
    if not path.exists(db_path):
        sys.exit(str(db_path) + " file does not exist, please sync with "
                "pycardsyncer first.")

    search_string = args['search_string'].decode("utf-8")

    my_dbtool = pycard.PcQuery(db_path, "utf-8", "stricts", False)

    #import:
    if args['importing']:
        cards = pycard.cards_from_file(args['importing'])
        for card in cards:
            my_dbtool.update(card, status=pycard.NEW)
        sys.exit()

    # backup:
    if args['backup']:
        with open(args['backup'], 'w') as vcf_file:
            if search_string == "":
                hreflist = my_dbtool.get_all_vref_from_db()
            else:
                hreflist = my_dbtool.search(search_string)
            for href in hreflist:
                vcard = my_dbtool.get_vcard_from_db(href)
                vcf_file.write(vcard.vcf)
        sys.exit()

    # editing a card:
    if (args['edit'] == True):
        href = my_dbtool.select_entry_urwid(args.search_string.decode('utf-8'))
        if href is None:
            sys.exit("Found no matching cards.")

    # print card(s)
    if (args['delete'] == True):
        href = my_dbtool.select_entry_urwid(args.search_string.decode('utf-8'))
        if href is None:
            sys.exit('Found no matching cards.')
        my_dbtool.mark_delete(href)
        print('vcard %s deleted from local db, will be deleted on ' % href + \
            'the server on the next sync')
        sys.exit()

    print("searching for " + args['search_string'] + "...")
    result = my_dbtool.search(args['search_string'].decode("utf-8"))
    for one in result:
        vcard = my_dbtool.get_vcard_from_db(one)
        if args['mutt']:
            lines = vcard.print_email()
        elif args['display_all']:
            lines = vcard.pretty
        else:
            lines = vcard.pretty_min
        if not lines == '':
            print(lines.encode('utf-8'))

    return 0

if __name__ == "__main__":
    main()
