#!/usr/bin/env python2
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
The pycarddav abstract model and tools for VCard handling.
"""

from __future__ import print_function

try:
    import base64
    import sys
    import vobject
    from collections import defaultdict

except ImportError, error:
    print(error)
    sys.exit(1)


def list_clean(string):
    """ transforms a comma seperated string to a list, stripping whitespaces
    "HOME, WORK,pref" -> ['HOME', 'WORK', 'pref']

    string: string of comma seperated elements
    returns: list()
    """

    string = string.split(',')
    rstring = list()
    for element in string:
        rstring.append(element.strip(' '))
    return rstring


NO_STRINGS = [u"n", "n", u"no", "no"]
YES_STRINGS = [u"y", "y", u"yes", "yes"]

PROPERTIES = ['EMAIL', 'TEL']
PROPS_ALL = ['FN', 'N', 'VERSION', 'NICKNAME', 'PHOTO', 'BDAY', 'ADR',
             'LABEL', 'TEL', 'EMAIL', 'MAILER', 'TZ', 'GEO', 'TITLE', 'ROLE',
             'LOGO', 'AGENT', 'ORG', 'NOTE', 'REV', 'SOUND', 'URL', 'UID',
             'KEY', 'CATEGORIES', 'PRODID', 'REV', 'SORT-STRING', 'SOUND',
             'URL', 'VERSION', 'UTC-OFFSET']
PROPS_ALLOWED = ['NICKNAME', 'BDAY', 'ADR', 'LABEL', 'TEL', 'EMAIL',
                 'MAILER', 'TZ', 'GEO', 'TITLE', 'ROLE', 'AGENT',
                 'ORG', 'NOTE', 'REV', 'SOUND', 'URL', 'UID', 'KEY',
                 'CATEGORIES', 'PRODID', 'REV', 'SORT-STRING', 'SOUND',
                 'URL', 'VERSION', 'UTC-OFFSET']
PROPS_ONCE = ['FN', 'N', 'VERSION']
PROPS_LIST = ['NICKNAME', 'CATEGORIES']
PROPS_BIN = ['PHOTO', 'LOGO', 'SOUND', 'KEY']


RTEXT = '\x1b[7m'
NTEXT = '\x1b[0m'
BTEXT = '\x1b[1m'

def get_names(display_name):
    first_name, last_name = '', display_name

    if display_name.find(',') > 0:
        # Parsing something like 'Doe, John Abraham'
        last_name, first_name = display_name.split(',')

    elif display_name.find(' '):
        # Parsing something like 'John Abraham Doe'
        # TODO: This fails for compound names. What is the most common case?
        name_list = display_name.split(' ')
        last_name = ''.join(name_list[-1])
        first_name = ' '.join(name_list[:-1])

    return first_name.strip().capitalize(), last_name.strip().capitalize()


def vcard_from_vobject(vcard):
    vdict = VCard()
    if vcard.name != "VCARD":
        raise Exception  # TODO proper Exception type
    for line in vcard.getChildren():
        # this might break, was tried/excepted before
        line.transformFromNative()
        property_name = line.name
        property_value = line.value

        try:
            if line.ENCODING_paramlist == [u'b']:
                property_value = base64.b64encode(line.value)

        except AttributeError:
            pass
        if type(property_value) == list:
            property_value = (',').join(property_value)

        vdict[property_name].append((property_value, line.params,))
    return vdict


def vcard_from_string(vcard_string):
    """
    vcard_string: str() or unicode()
    returns VCard()
    """
    try:
        vcard = vobject.readOne(vcard_string)
    except vobject.base.ParseError as error:
        raise Exception(error)  # TODO proper exception
    return vcard_from_vobject(vcard)


def vcard_from_email(display_name, email):
    fname, lname = get_names(display_name)
    vcard = vobject.vCard()
    vcard.add('n')
    vcard.n.value = vobject.vcard.Name(family=lname, given=fname)
    vcard.add('fn')
    vcard.fn.value = display_name
    vcard.add('email')
    vcard.email.value = email
    vcard.email.type_param = 'INTERNET'
    return vcard_from_vobject(vcard)


def cards_from_file(cards_f):
    collector = list()
    for vcard in vobject.readComponents(cards_f):
        collector.append(vcard_from_vobject(vcard))
    return collector


class VCard(defaultdict):
    """
    internal representation of a VCard. This is dict with some
    associated methods,
    each dict item is a list of tuples
    i.e.:
    >>> vcard['EMAIL']
    [('hanz@wurst.com', ['WORK', 'PREF']), ('hanz@wurst.net', ['HOME'])]


    h_ref: unique id (really just the url) of the VCard
    db_path: database file from which to initialize the VCard

    self.edited:
        0: nothing changed
        1: name and/or fname changed
        2: some property was deleted
    """

    def __init__(self, ddict=''):

        if ddict == '':
            defaultdict.__init__(self, list)
        else:
            defaultdict.__init__(self, list, ddict)
        self.href = ''
        self.edited = 0

    def serialize(self):
        return self.items().__repr__()

    @property
    def name(self):
        return unicode(self['N'][0][0]) if self['N'] else ''

    @name.setter
    def name(self, value):
        if not self['N']:
            self['N'] = [('', {})]
        self['N'][0][0] = value

    @property
    def fname(self):
        return unicode(self['FN'][0][0]) if self['FN'] else ''

    @fname.setter
    def fname(self, value):
        self['FN'][0] = (value, {})

    def alt_keys(self):
        keylist = self.keys()
        for one in [x for x in ['FN', 'N', 'VERSION'] if x in keylist]:
            keylist.remove(one)
        keylist.sort()
        return keylist

    def print_email(self):
        """prints only name, email and type for use with mutt"""
        collector = list()
        try:
            for one in self['EMAIL']:
                try:
                    typelist = ','.join(one[1][u'TYPE'])
                except KeyError:
                    typelist = ''
                collector.append(one[0] + "\t" + self.fname + "\t" + typelist)
            return '\n'.join(collector)
        except KeyError:
            return ''

    def print_tel(self):
        """prints only name, email and type for use with mutt"""
        collector = list()
        try:
            for one in self['TEL']:
                try:
                    typelist = ','.join(one[1][u'TYPE'])
                except KeyError:
                    typelist = ''
                collector.append(self.fname + "\t" + one[0] + "\t" + typelist)
            return '\n'.join(collector)
        except KeyError:
            return ''

    @property
    def pretty(self):
        return self._pretty_base(self.alt_keys())

    @property
    def pretty_min(self):
        return self._pretty_base(['TEL', 'EMAIL'])

    def _pretty_base(self, keylist):
        collector = list()
        collector.append('\n' + BTEXT + 'Name: ' + self.fname + NTEXT)
        for key in keylist:
            for value in self[key]:
                try:
                    types = ' (' + ', '.join(value[1]['TYPE']) + ')'
                except KeyError:
                    types = ''
                try:
                    line = key + types + ': ' + value[0]
                except UnicodeDecodeError:
                    line = key + types + ': ' + '<BINARY DATA>'
                collector.append(line)
        return '\n'.join(collector)

    def _line_helper(self, line):
        collector = list()
        for key in line[1].keys():
            collector.append(key + '=' + ','.join(line[1][key]))
        if collector == list():
            return ''
        else:
            return (';' + ';'.join(collector))

    @property
    def vcf(self):
        """serialize to VCARD as specified in RFC2624,
        if no UID is specified yet, one will be added (as a UID is mandatory
        for carddav as specified in RF6352
        TODO make shure this random uid is unique"""
        import string
        import random
        def generate_random_uid():
            """generate a random uid, when random isn't broken, getting a
            random UID from a pool of roughly 10^56 should be good enough"""
            choice = string.ascii_uppercase + string.digits
            return ''.join([random.choice(choice) for _ in range(36)])
        if 'UID' not in self.keys():
            self['UID'] = [(generate_random_uid(), dict())]
        collector = list()
        collector.append('BEGIN:VCARD')
        collector.append('VERSION:3.0')
        for key in ['FN', 'N']:
            collector.append(key + ':' + self[key][0][0])
        for prop in self.alt_keys():
            for line in self[prop]:

                types = self._line_helper(line)
                collector.append(prop + types + ':' + line[0])
        collector.append('END:VCARD')
        return '\n'.join(collector)
