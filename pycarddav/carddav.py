#!/usr/bin/env python
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
contains the class PyCardDAV and some associated functions and definitions
"""

from collections import namedtuple
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

import sys
import urlparse
import logging
import lxml.etree as ET


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


class UploadFailed(Exception):
    """uploading the card failed"""
    pass


class PyCardDAV(object):
    """class for interacting with a CardDAV server

    Since PyCardDAV relies heavily on Requests [1] its SSL verification is also
    shared by PyCardDAV [2]. For now, only the *verify* keyword is exposed
    through PyCardDAV.

    [1] http://docs.python-requests.org/
    [2] http://docs.python-requests.org/en/latest/user/advanced/

    raises:
        requests.exceptions.SSLError
        requests.exceptions.ConnectionError
        more requests.exceptions depending on the actual error
        Exception (shame on me)

    """

    class SSLAdapter(HTTPAdapter):
        """An HTTPS Transport Adapter that uses an arbitrary SSL version.

           Cory Benfield's solution as per http://lukasa.co.uk/2013/01/Choosing_SSL_Version_In_Requests/
        """
        def __init__(self, ssl_version=None, **kwargs):
            self.ssl_version = ssl_version
            super(PyCardDAV.SSLAdapter, self).__init__(kwargs)

        def init_poolmanager(self, connections, maxsize):
            self.poolmanager = PoolManager(num_pools=connections,
                                           maxsize=maxsize,
                                           ssl_version=self.ssl_version)


    def __init__(self, resource, debug='', user='', passwd='',
                 verify=True, write_support=False, auth='basic', ssl_version=None):
        #shutup url3
        urllog = logging.getLogger('requests.packages.urllib3.connectionpool')
        urllog.setLevel(logging.CRITICAL)

        split_url = urlparse.urlparse(resource)
        url_tuple = namedtuple('url', 'resource base path')
        self.url = url_tuple(resource,
                             split_url.scheme + '://' + split_url.netloc,
                             split_url.path)
        self.debug = debug
        self.session = requests.session()
        if ssl_version:
            self.session.mount('https://', PyCardDAV.SSLAdapter(ssl_version=ssl_version))
        self.write_support = write_support
        self._settings = {'verify': verify}
        if auth == 'basic':
            self._settings['auth'] = (user, passwd,)
        if auth == 'digest':
            from requests.auth import HTTPDigestAuth
            self._settings['auth'] = HTTPDigestAuth(user, passwd)
        self._default_headers = {"User-Agent": "pyCardDAV"}
        response = self.session.request('PROPFIND',
                                        self.url.resource,
                                        headers=dict(self.headers, **{'Depth': 1}),
                                        **self._settings)
        response.raise_for_status()   #raises error on not 2XX HTTP status code


    @property
    def verify(self):
        """gets verify from settings dict"""
        return self._settings['verify']

    @verify.setter
    def verify(self, verify):
        """set verify"""
        self._settings['verify'] = verify

    @property
    def headers(self):
        return dict(self._default_headers)

    def _check_write_support(self):
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
        response = requests.request('OPTIONS',
                                    self.url.base,
                                    headers=self.header)
        if "X-Sabre-Version" in response.headers:
            server = SABREDAV
        elif "X-DAViCal-Version" in response.headers:
            server = DAVICAL
        else:
            server = UNKNOWN
        logging.info(server + " detected")
        return server

    def get_abook(self):
        """does the propfind and processes what it returns

        :rtype: list of hrefs to vcards
        """
        xml = self._get_xml_props()
        abook = self._process_xml_props(xml)
        return abook

    def get_vcard(self, href):
        """
        pulls vcard from server

        :returns: vcard
        :rtype: string
        """
        response = self.session.get(self.url.base + href,
                                    headers=self.headers,
                                    **self._settings)
        response.raise_for_status()
        return response.content

    def update_vcard(self, card, href, etag):
        """
        pushes changed vcard to the server
        card: vcard as unicode string
        etag: str or None, if this is set to a string, card is only updated if
              remote etag matches. If etag = None the update is forced anyway
         """
         # TODO what happens if etag does not match?
        self._check_write_support()
        remotepath = str(self.url.base + href)
        headers = self.headers
        headers['content-type'] = 'text/vcard'
        if etag is not None:
            headers['If-Match'] = etag
        self.session.put(remotepath, data=card, headers=headers,
                         **self._settings)

    def delete_vcard(self, href, etag):
        """deletes vcard from server

        deletes the resource at href if etag matches,
        if etag=None delete anyway
        :param href: href of card to be deleted
        :type href: str()
        :param etag: etag of that card, if None card is always deleted
        :type href: str()
        :returns: nothing
        """
        # TODO: what happens if etag does not match, url does not exist etc ?
        self._check_write_support()
        remotepath = str(self.url.base + href)
        headers = self.headers
        headers['content-type'] = 'text/vcard'
        if etag is not None:
            headers['If-Match'] = etag
        result = self.session.delete(remotepath,
                                     headers=headers,
                                     **self._settings)
        response.raise_for_status()

    def upload_new_card(self, card):
        """
        upload new card to the server

        :param card: vcard to be uploaded
        :type card: unicode
        :rtype: tuple of string (path of the vcard on the server) and etag of
                new card (string or None)
        """
        self._check_write_support()
        card = card.encode('utf-8')
        for _ in range(0, 5):
            rand_string = get_random_href()
            remotepath = str(self.url.resource + rand_string + ".vcf")
            headers = self.headers
            headers['content-type'] = 'text/vcard'
            headers['If-None-Match'] = '*'
            response = requests.put(remotepath, data=card, headers=headers,
                                    **self._settings)
            if response.ok:
                parsed_url = urlparse.urlparse(remotepath)

                if response.headers['etag'] is None:
                    etag = ''
                else:
                    etag = response.headers['etag']

                return (parsed_url.path, etag)
        response.raise_for_status()

    def _get_xml_props(self):
        """PROPFIND method

        gets the xml file with all vcard hrefs

        :rtype: str() (an xml file)
        """
        headers = self.headers
        headers['Depth'] = '1'
        response = self.session.request('PROPFIND',
                                        self.url.resource,
                                        headers=headers,
                                        **self._settings)
        response.raise_for_status()
        if response.headers['DAV'].count('addressbook') == 0:
            raise Exception("URL is not a CardDAV resource")

        return response.content

    @classmethod
    def _process_xml_props(cls, xml):
        """processes the xml from PROPFIND, listing all vcard hrefs

        :param xml: the xml file
        :type xml: str()
        :rtype: dict() key: href, value: etag
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
                            if (props.tag == namespace + "getcontenttype" and
                                (props.text == "text/vcard" or
                                 props.text == "text/x-vcard" or
                                 props.text == "text/x-vcard; charset=utf-8")):
                                insert = True
                            if (props.tag == namespace + "getetag"):
                                etag = props.text
                        if insert:
                            abook[href] = etag
        return abook
