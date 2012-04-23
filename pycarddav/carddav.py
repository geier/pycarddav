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
    from os import path
    import StringIO
    import urlparse
    import pycurl
    import lxml.etree as ET
    from collections import namedtuple

except ImportError, error:
    print error
    sys.exit(1)


def get_random_href():
    """returns a random href"""
    import random
    tmp_list = list()
    for _ in xrange(3):
        rand_number = random.randint(0, 0x100000000)
        tmp_list.append("{0:x}".format(rand_number))
    return "-".join(tmp_list).upper()


def header_parser(header_string):
    """
    parses the HTTP header returned by the server

    Args:
        header_string: HTTP header as a string

    Returns:
        A dict, whose keywords correspond to the ones from the http header, the
        values a list of strings.

    example::

        {'Content-Length:': ['134'],
         'Content-Type:': ['text/xml; charset="utf-8"'],
         'DAV:': ['1',
                  '2',
                  '3',
                  'access-control',
                  'calendar-access',
                  'calendar-schedule',
                  'extended-mkcol',
                  'calendar-proxy',
                  'bind',
                  'addressbook',
                  'calendar-auto-schedule'],
         'Date:': ['Thu', '23 Feb 2012 00:03:11 GMT'],
         'HTTP/1.1': ['100 Continue', '412 Precondition Failed'],
         'Server:': ['Apache'],
         'X-DAViCal-Version:': ['DAViCal/1.0.2; DB/1.2.11'],
         'X-Powered-By:': ['PHP/5.3.10']}

    beware: not all keywords are followed by a ':'
    """

    head = dict()
    #import ipdb; ipdb.set_trace()
    for line in header_string.split("\r\n"):
        test = line.split(" ", 1)
        if not head.has_key(test[0]):
            head[test[0]] = list()
        try:
            for one in test[1].split(', '):
                head[test[0]].append(one)
        except IndexError:
            pass
    return head


DAVICAL = 'davical'
SABREDAV = 'sabredav'
UNKNOWN = 'unknown server'


class PyCardDAV(object):
    """interacts with CardDAV server"""

    def __init__(self, resource):
        split_url = urlparse.urlparse(resource)
        url_tuple = namedtuple('url', 'resource base path')
        login_creds = namedtuple('creds', 'user passwd resource')
        self.url = url_tuple(resource,
                             split_url.scheme + '://' + split_url.netloc,
                             split_url.path)
        self.debug = ""
        self.user = ""
        self.passwd = ""
        self.insecure_ssl = 0
        self.ssl_cacert_file = None
        self.curl = pycurl.Curl()
        self.response = StringIO.StringIO()
        self.header = StringIO.StringIO()
        self.write_support = False
        self._header = StringIO.StringIO()
        self.header = dict()

    def check_write_support(self):
        """checks if user really wants is data destroyed"""
        if not self.write_support:
            sys.stderr.write("Sorry, no write support for you. Please check the "
                             "documentation.\n")
            sys.exit(1)

    def _detect_server(self):
        """detects CardDAV server type

        currently supports davical and sabredav (same as owncloud)
        :rtype: string "davical" or "sabredav"
        """
        self._curl_reset()
        self.curl.setopt(pycurl.CUSTOMREQUEST, "OPTIONS")
        self.curl.setopt(pycurl.URL, self.url.base)
        self.perform_curl()
        print self.header
        if self.header.has_key("X-Sabre-Version:"):
            server =  SABREDAV
        elif self.header.has_key("X-DAViCal-Version:"):
            server = DAVICAL
        else:
            server = UNKNOWN
        if self.debug:
            print server + " detected"
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
        self._curl_reset()
        self.curl.setopt(pycurl.CUSTOMREQUEST, "GET")
        self.curl.setopt(pycurl.URL, self.url.base + vref)
        self.curl.perform()

        vcard = self.response.getvalue()
        return vcard

    def update_vcard(self, card, vref):
        """
        pushes changed vcard to the server
        card: vcard as unicode string
         """
        # TODO etag checking
        self.check_write_support()
        print str(vref), " uploading your changes..."
        self._curl_reset()
        remotepath = str(self.url.base + vref)

        headers = ["Content-Type: application/plain"]
        self.curl.setopt(pycurl.HTTPHEADER, headers)
        self.curl.setopt(pycurl.UPLOAD, 1)
        self.curl.setopt(pycurl.URL, remotepath)
        tempfile = StringIO.StringIO(card)
        self.curl.setopt(pycurl.READFUNCTION, tempfile.read)
        self.curl.setopt(pycurl.INFILESIZE, tempfile.len)

        self.curl.perform()
        #cleanup
        tempfile.close()
        self.curl.close()

    def delete_vcard(self, vref, etag, force=False):
        """deletes vcard from server

        deletes the resource at vref if etag matches, if force=True deletes even
        if etag does not match
        """
        # TODO implement delete_vcard
        pass

    def upload_new_card(self, card):
        """
        upload new card to the server

        :param card: vcard to be uploaded
        :type card: unicode
        :rtype: string, path of the vcard on the server
        """
        self.check_write_support()
        for _ in range(0, 5):
            rand_string = get_random_href()
            remotepath = str(self.url.resource + rand_string + ".vcf")
            self._curl_reset()
            # doesn't work without escape of *
            headers = ["If-None-Match: \*", "Content-Type: text/vcard"]
            self.curl.setopt(pycurl.HTTPHEADER, headers)
            self.curl.setopt(pycurl.UPLOAD, 1)
            self.curl.setopt(pycurl.URL, remotepath)
            #self.curl.setopt(pycurl.VERBOSE, 1)
            tempfile = StringIO.StringIO(card)
            self.curl.setopt(pycurl.READFUNCTION, tempfile.read)
            self.curl.setopt(pycurl.INFILESIZE, tempfile.len)
            #import ipdb; ipdb.set_trace()
            self.perform_curl()
            if self.header['HTTP/1.1'][-1] == '201 Created':
                parsed_url = urlparse.urlparse(remotepath)
                return parsed_url.path
            # TODO: should raise an exception if this is ever reached

    def _curl_reset(self):
        """
        resets the connection, called from within the other
        functions interacting with the CardDAV server
        """
        self.curl = pycurl.Curl()
        self.response = StringIO.StringIO()
        self._header = StringIO.StringIO()
        self.curl.setopt(pycurl.WRITEFUNCTION, self.response.write)
        self.curl.setopt(pycurl.HEADERFUNCTION, self._header.write)
        self.curl.setopt(pycurl.SSLVERSION, pycurl.SSLVERSION_SSLv3)
        self.curl.setopt(pycurl.USERPWD, self.user + ":" + self.passwd)
        if (self.insecure_ssl == 1):
            self.curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        if self.ssl_cacert_file:
            self.curl.setopt(pycurl.CAINFO, path.expanduser(self.ssl_cacert_file))

    def perform_curl(self):
        """performs curl request and exits gracefully on failure"""
        try:
            self.curl.perform()
        except pycurl.error, errorstring:
            sys.stderr.write( str(errorstring[1])+"\n")
            sys.exit(1)
        self.header = header_parser(self._header.getvalue())

    def _get_xml_props(self):
        """PROPFIND method

        gets the xml file with all vcard hrefs

        :rtype: str() (an xml file)
        """
        self._curl_reset()
        self.curl.setopt(pycurl.CUSTOMREQUEST, "PROPFIND")
        self.curl.setopt(pycurl.URL, self.url.resource)
        self.perform_curl()
        try:
            if self.header['DAV:'].count('addressbook') == 0:
                print "URL is not a CardDAV resource"
                sys.exit(1)
        except KeyError:
            print "URL is not a DAV resource"
            sys.exit(1)
        return self.response.getvalue()

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
                            if (props.tag == namespace + "getcontenttype" and ( props.text == "text/vcard" or props.text == "text/x-vcard" )) :
                                insert = True
                            if (props.tag == namespace + "getetag"):
                                etag = props.text
                            #print("%s - %s" % (props.tag, props.text))
                        if insert:
                            abook[href] = etag
        return abook
