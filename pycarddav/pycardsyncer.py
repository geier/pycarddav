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

    from ConfigParser import SafeConfigParser, NoOptionError
    import vobject
except ImportError, error:
    print error
    sys.exit(1)

LEVELS = { 'debug':logging.DEBUG,
           'info':logging.INFO,
            'warning':logging.WARNING,
            'error':logging.ERROR,
            'critical':logging.CRITICAL,
         }


def smartencode(string):
    """convert everything to utf-8"""
    return unicode(string).encode("utf-8", "strict")


def signal_handler(*_):
    """this should hide ugly backtraces when hitting ctrl-c"""
    sys.exit(0)


def main():
    """this should probably be seperated from the class definitions"""
    # trying to hide some ugly python code on pressing Ctrl-C
    logging.basicConfig(level=logging.DEBUG)
    signal.signal(signal.SIGINT, signal_handler)

    arg_parser = argparse.ArgumentParser(
            description="syncs the local db to the CardDAV server")
    arg_parser.add_argument(
        "-c", "--config", action="store", dest="configfile",
        default="~/.pycard/pycard.conf",
        help="defaults to ~/.pycard/pycard.conf")
    arg_parser.add_argument("-v", "--version", action="version",
            version=pycarddav.__version__)
    arg_parser.add_argument("--debug", action="store_true", dest="debug",
            help="enable debugging; WARNING: shows passwords in cleartext")
    args = arg_parser.parse_args()

    logger = logging.getLogger('simple_logger')
    logger.setLevel(logging.DEBUG)

    #config file foo
    configfile = path.expanduser(args.configfile)
    logging.info("reading config from %s" % configfile)
    conf_parser = SafeConfigParser()
    conf_parser.read(configfile)

    resource = conf_parser.get('default', 'resource')
    syncer = carddav.PyCardDAV(resource, )
    syncer.user = conf_parser.get('default', 'user')
    try:
        syncer.passwd = conf_parser.get('default', 'passwd')
    except NoOptionError:
        syncer.passwd = getpass.getpass(prompt='CardDAV password: ')
    try:
        temp = conf_parser.get('default', 'write_support')
        if temp == 'YesPleaseIDoHaveABackupOfMyData':
            syncer.write_support = True
    except NoOptionError:
        pass

    debug = bool(conf_parser.getint('default', 'DEBUG'))
    if args.debug:   # argument overrides config file
        debug = bool(args.debug)
    db_path = conf_parser.get('default', 'db_path')
    # ssl:
    try:
        syncer.insecure_ssl = conf_parser.getint('default', 'insecure_ssl')
    except NoOptionError:
        pass
    try:
        syncer.ssl_cacert_file = conf_parser.get('default', 'ssl_cacert_file')
    except NoOptionError:
        pass
    syncer.debug = debug

    logging.info("using remote options:\n"
        "  user: %s\n" % syncer.user + \
        "  passwd: %s\n" % syncer.passwd + \
        "  resource: %s\n" % syncer.url.resource + \
        "  base_url: %s\n" % syncer.url.base + \
        "  insecureSSL: %s\n" % syncer.insecure_ssl +\
        "using local options:\na" + \
        "  db_path: %s\n" % db_path)

    my_dbtool = pycard.PcQuery(db_path, "utf-8", "stricts", debug)

    # sync:
    abook = syncer.get_abook()  # type (abook): dict

    for vref, v_etag in abook.iteritems():
        if my_dbtool.check_vref_exists(vref):
            my_dbtool.insert_vref(vref)

        if my_dbtool.check_new_etag(vref, v_etag):
            my_dbtool.delete_vcard_props_from_db(vref)
            logging.debug("getting ", vref, " etag: ", v_etag)
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
        logging.info("trying to update %s" % href)
        card = my_dbtool.get_vcard_from_db(href)
        logging.debug("%s" % my_dbtool.get_etag(href))
        syncer.update_vcard(card.serialize(), href, None)
        my_dbtool.reset_flag(href)
    hrefs = my_dbtool.get_local_new_hrefs()
    for href in hrefs:
        logging.info("trying to upload new card %s" % href)
        card = my_dbtool.get_vcard_from_db(href)
        href_new = syncer.upload_new_card(card.serialize())
        my_dbtool.update_vref(href, href_new)
        my_dbtool.reset_flag(href_new)


if __name__ == "__main__":
    main()
