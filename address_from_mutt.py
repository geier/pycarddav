#!/usr/bin/env python
# coding: utf-8
import sys
import email
import email.header
import re


def get_email(string):
    try:
    # looking for: hanz wurst <hanz@wurst.com>
        pattern = r'<([^"]*)>'
        m = re.search(pattern, string)
        print '3'
        return m.group().strip('<').strip('>')
    except AttributeError:
        pass
    return string  # don't know what to do, giving up


def get_names(string):
    fname, mname, fname = '', '', ''
    names = string  # just for backup

    if string.find('"') > -1:  # looking for "names here" <hanz@mail.com>
        pattern = r'"([^"]*)"'
        m = re.search(pattern, string)
        names = m.group().strip('"')
        print '4'
    else:
        try:  # looking for: hanz wurst <hanz@mail.com>
            pattern = r'<([^"]*)>'
            m = re.search(pattern, string)
            names = string[:m.start()].strip()
            print '9'

        except AttributeError:
            pass




    # names should now only include the names
    if names.find(',') > 0:  # prop: "lastname, first names"
        print '5'
        names = names.split(',')
        lname = names[0].strip()
        fname = names[1].strip()

        pass
    elif names.find(' '):
        print '6'
        print names
        name_list = names.split(' ')
        lname = ''.join(name_list[-1])
        fname = ' '.join(name_list[:-1])
    else:
        lname = names
        print '7'

    return fname, '', lname


def parse_email(string):
    email_address = ''
    fname = ''
    lname = ''
    mname = ''

    address_string = list()
    addresses = email.header.decode_header(string)
    for string, enc in addresses:
        try:
            string = string.decode(enc)
        except TypeError:
            string = unicode(string)
        address_string.append(string)

    address_string = ' '.join(address_string)

    if address_string.find('@') == -1:  # no '@'? prob. no valid email address
        print '1'
        return (address_string, fname, mname, lname)

    if address_string.find(' ') == -1:  # no ' ': probably only email address
        address_string.strip().strip('<').strip('>')
        # FIXME somehow, some '<' seem to survive this...
        print '2'
        return (address_string, fname, mname, lname)
    # looks like it's more complicated, trying to find email address and
    # names seperately
    email_address = get_email(address_string)
    fname, mname, lname = get_names(address_string)

    return (email_address, fname, mname, lname)

mail = sys.stdin.read()
msg = email.message_from_string(mail)
address = msg['From']
print 'xxx' + address + 'xxx'
email_address, fname, mname, lname = parse_email(address)



print 'email: ' + email_address
print 'lname: ' + lname
print 'fname: ' + fname
print 'mname: ' + mname
