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
from __future__ import print_function

#try:
from netrc import netrc
from urlparse import urlsplit
from pycarddav import Configuration, ConfigurationParser
from pycarddav import capture_user_interruption
from pycarddav import pycard
from pycarddav import carddav

import getpass
import logging
import sys

#except ImportError, error:
#    sys.stderr.write(error)
#    sys.exit(1)

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL,
          }


class SyncConfigurationParser(ConfigurationParser):
    """A specialized setup tool for synchronization."""
    def __init__(self):
        ConfigurationParser.__init__(self, "syncs the local db to the CardDAV server")
        self.set_mandatory_options([(Configuration.SECTIONS.DAV, 'resource'),
                                    (Configuration.SECTIONS.DB, 'path')])

    def check(self, conf):
        success = ConfigurationParser.check(self, conf)

        if success and not conf.dav__passwd:
            hostname = urlsplit(conf.dav__resource).hostname
            auths = netrc().authenticators(hostname)
            if auths:
                if not conf.dav__user or auths[0] == conf.dav__user:
                    logging.debug("Read password for user %s on %s in .netrc",
                                  auths[0], hostname)
                    conf.dav__user = auths[0]
                    conf.dav__passwd = auths[2]
                else:
                    logging.error("User %s not found for %s in .netrc",
                                  conf.dav__user, hostname)
                    success = False
            elif conf.dav__user:
                conf.dav__passwd = getpass.getpass(prompt='CardDAV password: ')
            else:
                logging.error("Missing credentials for %s", hostname)
                success = False

        return success


def main():
    """this should probably be seperated from the class definitions"""
    capture_user_interruption()

    # Read configuration.
    parser = SyncConfigurationParser()

    conf = parser.parse()
    if conf is None:
        sys.exit(1)

    if conf.debug:
        conf.dump()

    syncer = carddav.PyCardDAV(conf.dav__resource,
                               user=conf.dav__user,
                               passwd=conf.dav__passwd,
                               write_support=conf.write_support,
                               verify = conf.dav__verify)

    my_dbtool = pycard.PcQuery(conf.sqlite__path, "utf-8", "stricts", conf.debug)

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
    # uploading
    hrefs = my_dbtool.get_new()
    for href in hrefs:
        logging.info("trying to upload new card %s", href)
        card = my_dbtool.get_vcard_from_db(href)
        (href_new, etag_new) = syncer.upload_new_card(card.vcf)
        my_dbtool.update_href(href, href_new)
        remote_changed = True

    # deleting locally deleted cards on the server
    hrefs_etags = my_dbtool.get_marked_delete()
    for href, etag in hrefs_etags:
        logging.info('trying to delete card %s', href)
        syncer.delete_vcard(href, etag)
        my_dbtool.rm_from_deleted(href)
        remote_changed = True

    # detecting remote-deleted cards
    ulist = list()
    # is there a better way to compare a list of unicode() with a list of str()
    # objects?
    if remote_changed:
        abook = syncer.get_abook()  # type (abook): dict
    for one in abook.keys():
        ulist.append(unicode(one))
    rlist = my_dbtool.get_all_vref_from_db()
    delete = set(rlist).difference(ulist)
    for href in delete:
        my_dbtool.delete_vcard_from_db(href)

if __name__ == "__main__":
    main()
