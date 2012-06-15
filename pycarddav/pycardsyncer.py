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


try:
    import sys
    import argparse
    import signal
    import getpass
    from os import path
    import pycard
    import pycarddav
    import carddav
    import logging
    from ConfigParser import SafeConfigParser
    import vobject
except ImportError, error:
    sys.stderr.write(error)
    sys.exit(1)

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL,
          }


def smartencode(string):
    """convert everything to utf-8"""
    return unicode(string).encode("utf-8", "strict")


def signal_handler(*_):
    """this should hide ugly backtraces when hitting ctrl-c"""
    sys.exit(0)


def parser():
    """config and command line option parser for pycardsyncer"""
    carg_parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False
            )
    carg_parser.add_argument("-c", "--config",
        action="store", dest="configfile",
        default="~/.pycard/pycard.conf", metavar="FILE",
        help="defaults to ~/.pycard/pycard.conf")
    args, remaining_argv = carg_parser.parse_known_args()

    config_parser = SafeConfigParser(vars(args))
    config_parser.read([path.expanduser(args.configfile)])
    defaults = dict(config_parser.items("default"))

    arg_parser = argparse.ArgumentParser(
            description="syncs the local db to the CardDAV server")
    arg_parser.set_defaults(**defaults)
    arg_parser.add_argument("-v", "--version", action="version",
            version=pycarddav.__version__)
    arg_parser.add_argument("--debug", action="store_true", dest="debug",
            help="enable debugging; WARNING: shows passwords in cleartext")
    args = vars(arg_parser.parse_args(remaining_argv))
    if 'passwd' not in args:
        args['passwd'] = getpass.getpass(prompt='CardDAV password: ')
    try:
        if args['write_support'] == 'YesPleaseIDoHaveABackupOfMyData':
            args['write_support'] = True
        else:
            args['write_support'] = False
    except KeyError:
        args['write_support'] = False
    return args


def main():
    """this should probably be seperated from the class definitions"""
    # trying to hide some ugly python code on pressing Ctrl-C
    logging.basicConfig(level=logging.DEBUG)
    signal.signal(signal.SIGINT, signal_handler)
    args = parser()

    logger = logging.getLogger('simple_logger')
    logger.setLevel(logging.DEBUG)

    syncer = carddav.PyCardDAV(args['resource'],
                               user=args['user'],
                               passwd=args['passwd'],
                               write_support=args['write_support'])
    try:
        syncer.insecure_ssl = args['insecure_ssl']
    except KeyError:
        pass
    try:
        syncer.ssl_cacert_file = args['ssl_cacert_file']
    except KeyError:
        pass

    logging.debug("using remote options:\n"
        "  user: %s\n" % syncer.user + \
        "  passwd: %s\n" % syncer.passwd + \
        "  resource: %s\n" % syncer.url.resource + \
        "  base_url: %s\n" % syncer.url.base + \
        "  insecureSSL: %s\n" % syncer.insecure_ssl +\
        "using local options:\n" + \
        "  db_path: %s\n" % args['db_path'])

    my_dbtool = pycard.PcQuery(args['db_path'], "utf-8", "stricts",
                               args['debug'])

    # sync:
    abook = syncer.get_abook()  # type (abook): dict

    for vref, v_etag in abook.iteritems():
        if my_dbtool.check_vref_exists(vref):
            my_dbtool.insert_vref(vref)

        if my_dbtool.check_new_etag(vref, v_etag):
            my_dbtool.delete_vcard_props_from_db(vref)
            logging.debug("getting %s etag: %s", vref, v_etag)
            vcard = syncer.get_vcard(vref)
            vcard = vobject.readOne(vcard)
            my_dbtool.insert_vcard_in_db(vref, vcard)
            my_dbtool.update_etag(vref, v_etag)

    # detecting remote-deleted cards
    ulist = list()
    # is there a better way to compare a list of unicode() with a list of str()
    # objects?
    for one in abook.keys():
        ulist.append(unicode(one))
    rlist = my_dbtool.get_all_vref_from_db()
    delete = set(rlist).difference(ulist)
    #import ipdb; ipdb.set_trace()
    for href in delete:
        my_dbtool.delete_vcard_from_db(href)

    # for now local changes overwritten by remote changes
    logging.info("getting changed vcards from db")
    hrefs = my_dbtool.get_local_edited_hrefs()
    for href in hrefs:
        logging.info("trying to update %s", href)
        card = my_dbtool.get_vcard_from_db(href)
        card_string = card.serialize()
        card_string = card_string.replace('###COMMA###', ',')
        logging.debug("%s", my_dbtool.get_etag(href))
        syncer.update_vcard(card_string, href, None)
        my_dbtool.reset_flag(href)
    hrefs = my_dbtool.get_local_new_hrefs()
    for href in hrefs:
        logging.info("trying to upload new card %s", href)
        card = my_dbtool.get_vcard_from_db(href)
        card_string = card.serialize()
        card_string = card_string.replace('###COMMA###', ',')
        href_new = syncer.upload_new_card(card_string)
        my_dbtool.update_vref(href, href_new)
        my_dbtool.reset_flag(href_new)

    # deleting locally deleted cards on the server
    hrefs_etags = my_dbtool.get_local_deleted_hrefs_etags()
    for href, etag in hrefs_etags:
        logging.info('trying to delete card %s', href)
        syncer.delete_vcard(href, etag)
        my_dbtool.rm_from_deleted(href)


if __name__ == "__main__":
    main()
