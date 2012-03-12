#!/usr/bin/env python
# coding: utf-8
# vim: set ts=4 sw=4 expandtab sts=4:
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <geier@lostpackets.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Christian Geier
# ----------------------------------------------------------------------------


#from IPython.Debugger import Tracer; debug_here = Tracer()
try:
    import sys
    import argparse
    import signal
    import getpass
    from os import path
    import pycard
    import pycarddav

    from ConfigParser import SafeConfigParser, NoOptionError
    import vobject
except ImportError, error:
    print error
    sys.exit(1)


def smartencode(string):
    """convert everything to utf-8"""
    return unicode(string).encode("utf-8", "strict")


def signal_handler(*_):
    """this should hide ugly backtraces when hitting ctrl-c"""
    sys.exit(0)



def main():
    """this should probably be seperated from the class definitions"""
    # trying to hide some ugly python code on pressing Ctrl-C
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

    #config file foo
    configfile = path.expanduser(args.configfile)
    if args.debug:
        print "reading config from ", configfile
    conf_parser = SafeConfigParser()
    conf_parser.read(configfile)

    resource = conf_parser.get('default', 'resource')
    syncer = pycard.PyCardDAV(resource, )
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

    if debug:
        print "using remote options:"
        print "  user:", syncer.user
        print "  passwd:", syncer.passwd
        print "  resource:", syncer.url.resource
        print "  base_url:", syncer.url.base
        print "  insecureSSL:", syncer.insecure_ssl
        print "using local options:"
        print "  db_path:", db_path
        print "\n"

    my_dbtool = pycard.PcQuery(db_path, "utf-8", "stricts", debug)

    # sync:
    abook = syncer.get_abook()

    for vref, v_etag in abook.iteritems():
        if my_dbtool.check_vref_exists(vref):
            my_dbtool.insert_vref(vref)

        if my_dbtool.check_new_etag(vref, v_etag):
            my_dbtool.delete_vcard_props_from_db(vref)
            if debug:
                print "getting ", vref, " etag: ", v_etag
            vcard = syncer.get_vcard(vref)
            vcard = vobject.readOne(vcard)
            # import ipdb; ipdb.set_trace()
            my_dbtool.insert_vcard_in_db(vref, vcard)
            my_dbtool.update_etag(vref, v_etag)
    # for now local changes overwritten by remote changes
    if debug:
        print "getting changed vcards from db"
    hrefs = my_dbtool.get_local_edited_hrefs()
    for href in hrefs:
        if debug:
            print "trying to update " + href
        card = my_dbtool.get_vcard_from_db(href)
        syncer.update_vcard(card.serialize(), href)
        my_dbtool.reset_flag(href)
    hrefs = my_dbtool.get_local_new_hrefs()
    for href in hrefs:
        if debug:
            print "trying to upload new card " + href
        card = my_dbtool.get_vcard_from_db(href)
        href_new = syncer.upload_new_card(card.serialize())
        my_dbtool.update_vref(href, href_new)
        my_dbtool.reset_flag(href_new)


if __name__ == "__main__":
    main()
