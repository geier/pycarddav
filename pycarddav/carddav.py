#!/usr/bin/env python
# vim: set ts=4 sw=4 expandtab sts=4:
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <geier@lostpackets.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Christian Geier
# ----------------------------------------------------------------------------
"""
classes and methods for pycarddav, the carddav class could/should be moved
to another module for better reusing
"""
try:
    import sys
    import urlparse
    import lxml.etree as ET
    from collections import namedtuple
    import requests

except ImportError, error:
    sys.stderr.write(error)
    sys.exit(1)


def get_random_href():
    """returns a random href"""
    import random
    tmp_list = list()
    for _ in xrange(3):
        rand_number = random.randint(0, 0x100000000)
        tmp_list.append("{0:x}".format(rand_number))
    return "-".join(tmp_list).upper()


DAVICAL = 'davical'
SABREDAV = 'sabredav'
UNKNOWN = 'unknown server'


class PyCardDAV(object):
    """interacts with CardDAV server"""

    def __init__(self, resource, debug='', user='', passwd='',
                insecure_ssl=False, ssl_cacert_file='', write_support=False):
        split_url = urlparse.urlparse(resource)
        url_tuple = namedtuple('url', 'resource base path')
        self.url = url_tuple(resource,
                             split_url.scheme + '://' + split_url.netloc,
                             split_url.path)
        self.debug = debug
        self.user = user
        self.passwd = passwd
        self.settings = {'auth': (user, passwd,)}
        self.ssl_cacert_file = ssl_cacert_file
        self.session = requests.session()
        self.write_support = write_support
        self.insecure_ssl = insecure_ssl

    def _set_insecure_ssl(self, insecure):
        if insecure is True or 1:
            self.settings['verify'] = False
        else:
            self.settings['verify'] = True

    def _get_insecure_ssl(self):
        return self.settings['verify']

    insecure_ssl = property(_get_insecure_ssl, _set_insecure_ssl)
    del _get_insecure_ssl, _set_insecure_ssl

    def check_write_support(self):
        """checks if user really wants his data destroyed"""
        if not self.write_support:
            sys.stderr.write("Sorry, no write support for you. Please check "
                             "the documentation.\n")
            sys.exit(1)

    def _detect_server(self):
        """detects CardDAV server type

        currently supports davical and sabredav (same as owncloud)
        :rtype: string "davical" or "sabredav"
        """
        response = requests.request('OPTIONS', self.url.base)
        if "X-Sabre-Version" in response.headers:
            server = SABREDAV
        elif "X-DAViCal-Version" in response.headers:
            server = DAVICAL
        else:
            server = UNKNOWN
        if self.debug:  # TODO proper logging
            print(server + " detected")
        return server

    def get_abook(self):
        """does the propfind and processes what it returns

        :rtype: list of hrefs to vcards
        """
        xml = self._get_xml_props()
        abook = self._process_xml_props(xml)
        return abook

    def get_vcard(self, vref):
        """
        pulls vcard from server
        returns vcard
        """
        response = self.session.get(self.url.base + vref, **self.settings)
        return response.content

    def update_vcard(self, card, vref, etag):
        """
        pushes changed vcard to the server
        card: vcard as unicode string
        etag: str or None, if this is set to a string, card is only updated if
              remote etag matches. If etag = None the update is forced anyway
         """
         # TODO what happens if etag does not match?
        self.check_write_support()
        remotepath = str(self.url.base + vref)
        headers = {'content-type': 'text/vcard'}
        if etag is not None:
            headers['If-Match'] = etag
        self.session.put(remotepath, data=card, headers=headers,
                          **self.settings)

    def delete_vcard(self, vref, etag):
        """deletes vcard from server

        deletes the resource at vref if etag matches,
        if etag=None delete anyway
        :param vref: vref of card to be deleted
        :type vref: str()
        :param etag: etag of that card, if None card is always deleted
        :type vref: str()
        :returns: nothing
        """
        # TODO: what happens if etag does not match, url does not exist etc ?
        self.check_write_support()
        remotepath = str(self.url.base + vref)
        headers = {'content-type': 'text/vcard'}
        if etag is not None:
            headers['If-Match'] = etag
        self.session.delete(remotepath, headers=headers, **self.settings)

    def upload_new_card(self, card):
        """
        upload new card to the server

        :param card: vcard to be uploaded
        :type card: unicode
        :rtype: tuple of string (path of the vcard on the server) and etag of
                new card (string or None)
        """
        self.check_write_support()
        for _ in range(0, 5):
            rand_string = get_random_href()
            remotepath = str(self.url.resource + '/' + rand_string + ".vcf")
            headers = {'content-type': 'text/vcard', 'If-None-Match': '*'}
            response = requests.put(remotepath, data=card, headers=headers,
                                        **self.settings)
            if response.ok:
                parsed_url = urlparse.urlparse(remotepath)

                if response.headers['etag'] is None:
                    etag = ''
                else:
                    etag = response.headers['etag']

                return (parsed_url.path, etag)
            # TODO: should raise an exception if this is ever reached

    def _get_xml_props(self):
        """PROPFIND method

        gets the xml file with all vcard hrefs

        :rtype: str() (an xml file)
        """

        response = requests.request('PROPFIND', self.url.resource,
                                    **self.settings)
        try:
            if response.headers['DAV'].count('addressbook') == 0:
                sys.stderr.write("URL is not a CardDAV resource")
                sys.exit(1)
        except AttributeError:
            print("URL is not a DAV resource")
            sys.exit(1)
        return response.content

    def _process_xml_props(self, xml):
        """processes the xml from PROPFIND, listing all vcard hrefs

        :param xml: the xml file
        :type xml: str()
        :rtype: dict() key: vref, value: etag
        """
        namespace = "{DAV:}"

        element = ET.XML(xml)
        abook = dict()
        for response in element.iterchildren():
            if (response.tag == namespace + "response"):
                href = ""
                etag = ""
                insert = False
                for refprop in response.iterchildren():
                    if (refprop.tag == namespace + "href"):
                        href = refprop.text
                    for prop in refprop.iterchildren():
                        for props in prop.iterchildren():
                            if (props.tag == namespace + "getcontenttype" and \
                               (props.text == "text/vcard" or \
                                props.text == "text/x-vcard")):
                                insert = True
                            if (props.tag == namespace + "getetag"):
                                etag = props.text
                        if insert:
                            abook[href] = etag
        return abook
