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

try:
    import sys
    import signal
    from os import path
    import argparse
    from ConfigParser import SafeConfigParser
    import pycard
    import vobject
    import __init__
except ImportError, error:
    print(error)
    sys.exit(1)

try:
    from termcolor import cprint

    def print_bold(text):
        """prints text bold"""
        cprint(text, attrs=['bold'])
except ImportError:

    def print_bold(text):
        """prints text bold"""
        print(text)


def signal_handler(signal, frame):
    """
    tries to hide some ugly python backtraces from the user after
    pressing ctrl-c
    """
    sys.exit(0)


def main():
    """main function, everything starts  here"""
    configfile = "~/.pycard/pycard.conf"

    parser = argparse.ArgumentParser(
        description='prints contacts cards matching a search string')
    parser.add_argument("-v", "--version", action="version",
            version=__init__.__version__)
    parser.add_argument(
        "-c", "--config", action="store", dest="configfile",
        default="~/.pycard/pycard.conf",
        help="defaults to ~/.pycard/pycard.conf")
    parser.add_argument("-a", action="store_true", dest="display_all",
            default="False", help="prints the whole card, not only name, "
            "telephone numbers and email addresses")
    parser.add_argument("-m", dest="print_function", action="store_const",
            const="print_email", default="print_contact_info",
            help="only prints email addresses, in a mutt friendly format")
    parser.add_argument("-e", dest="edit", action="store_true",
            default="False", help="edit the contact file.\n"
            "NOTE: this feature is experimental and will probably corrupt "
            "your *local* database. Your remote CardDAV resource will stay "
            "untouched, as long as You don't enable write support for the "
            "syncer.")
    parser.add_argument("--debug", action="store_true", dest="debug",
            default="False", help="enable debugging")
    parser.add_argument("search_string", metavar="SEARCHSTRING",
            help="the string to search for", nargs='?', default="")
    parser.add_argument("-b", "--backup", action="store",
            dest="backup", help="backup the local db to BACKUP, "
            "if a SEARCHSTRING is present, only backup cards matching it.")
    parser.add_argument('-i', '--import', type=argparse.FileType('r'),
            dest='importing', help='import vcard from file or STDIN')
    parser.add_argument('--delete', dest='delete', action='store_true',
            help='delete card matching SEARCHSTRING')
    args = parser.parse_args()

    # let's try to hide some ugly python code, at least when hitting Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)
    configfile = path.expanduser(args.configfile)

    parser = SafeConfigParser()
    parser.read(configfile)
    db_path = path.expanduser(parser.get('default', 'db_path'))
    # testing if the db exists
    if not path.exists(db_path):
        sys.exit(str(db_path) + " file does not exist, please sync with "
                "pycardsyncer first.")

    my_query = pycard.PcQuery()
    my_query.db_path = path.expanduser(db_path)
    my_query.debug = args.debug

    search_string = args.search_string.decode("utf-8")

    my_dbtool = pycard.PcQuery(db_path, "utf-8", "stricts", False)

    #import:
    if args.importing:
        for vcard in vobject.readComponents(args.importing):
            vcard.prettyPrint()
            while True:
                answer = raw_input("Import this card [y/n]? ")
                if answer.lower() in pycard.NO_STRINGS:
                    break
                if answer.lower() in pycard.YES_STRINGS:
                    while True:
                        tmp_vref = pycard.get_random_href()
                        #import ipdb; ipdb.set_trace()
                        if my_dbtool.check_vref_exists(tmp_vref):
                            my_dbtool.insert_vref(tmp_vref, 2)
                            break
                    my_dbtool.insert_vcard_in_db(tmp_vref, vcard)
                    break
        sys.exit()

    # backup:
    if args.backup:
        vcf_file = open(args.backup, 'w')
        if search_string == "":
            hreflist = my_dbtool.get_all_vref_from_db()
        else:
            hreflist = my_dbtool.get_contact_id_from_string(search_string)
        for href in hreflist:

            card = my_dbtool.get_vcard_from_db(href)
            card_string = card.serialize()
            card_string = card_string.replace('###COMMA###', ',')
            vcf_file.write(card_string)
        sys.exit()

    # editing a card:
    if (args.edit == True):
        href = my_query.select_entry_urwid(args.search_string.decode('utf-8'))
        if href is None:
            sys.exit("Found no matching cards.")

        contact = pycard.VCard(href, db_path)
        while True:
            contact.edit()
            for prop in contact:
                if prop.edited == 1:
                    contact.edited = 1
            print("")
            contact.print_contact_info(True)
            while 1:
                edit = raw_input("Is this correct [y/N]? ")
                if edit in [u"y", "y", u"Y", "Y"]:
                    contact.save()
                    sys.exit()
                if edit in [u"n", "n", u"N", "N"]:
                    return 0
        return 0

    if (args.delete == True):
        href = my_query.select_entry_urwid(args.search_string.decode('utf-8'))
        if href is None:
            sys.exit('Found no matching cards.')
        my_query.mark_for_deletion(href, '')
        my_query.delete_vcard_from_db(href)
        print(('vcard %s deleted from local db, will be deleted on ' %href + \
            'the server on the next sync'))
        sys.exit()


    my_query.print_function = args.print_function
    my_query.display_all = args.display_all

    print(("searching for " + args.search_string + "..."))
    my_query.search(args.search_string.decode("utf-8"))

    return 0

if __name__ == "__main__":
    main()
