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


Database Layout
===============

current version number: 6
tables: version, vcardtable, properties, blobproperties

version:
    version (INT): only one line: current db version

vcardtable:
    href (TEXT)
    etag (TEXT)
    name (TEXT): name as in vcard, seperated by ';'
    fname (TEXT): formated name
    status (INT): status of this card
        * 0: OK; not touched since last sync
        * 1: NEW; new card, needs to be created on the server
        * 2: CHANGED; properties edited or added (news to be pushed to server)
        * 9: DELETED; marked for deletion (needs to be deleted on server)
    vcard (TEXT) the content of the vcard minus any binary objects
                as __repr__() of the object

"""

from __future__ import print_function

try:
    import sys
    import ast
    import urwid
    import sqlite3
    import vobject
    import logging
    from os import path
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


class SelText(urwid.Text):
    """
    Selectable Text with an aditional href varibale
    """
    def __init__(self, text, href):
        urwid.Text.__init__(self, text)
        self.href = href

    def selectable(self):
        """needs to be implemented"""
        return True

    def keypress(self, _, key):
        """needs to be implemented"""
        return key


class SelectedButton(Exception):
    def __init__(self, exit_token=None):
        self.exit_token = exit_token


class Selected(Exception):
    """
    used for signalling that an item was chosen in urwid
    """
    pass


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


OK = 0
NEW = 1
CHANGED = 2
DELETED = 9

RTEXT = '\x1b[7m'
NTEXT = '\x1b[0m'
BTEXT = '\x1b[1m'


def vcard_from_vobject(vcard):
    vdict = VCard()
    if vcard.name != "VCARD":
        raise Exception
    for line in vcard.getChildren():
        # this might break, was tried/excepted before
        line.transformFromNative()
        property_name = line.name
        property_value = line.value

        try:
            if line.ENCODING_paramlist == [u'b']:
                print("found binary")
#                stuple = (unicode(property_name),
#                            sqlite3.Binary(property_value),
#                            vref, unicode(line.params),)
#                cursor.execute('INSERT INTO blobproperties '
#                        '(property, value, href, parameters) '
#                        'VALUES (?,?,?,?);', stuple)
#                conn.commit()

        except AttributeError:
            #if property_name in [u'FN', u'N', u'VERSION']:
            #    continue
            if type(property_value) == list:
                property_value = (',').join(property_value)
            #stuple = (unicode(property_name), property_value,
            #            vref, unicode(line.params),)

            vdict[property_name].append((property_value, line.params,))
    return vdict


def vcard_from_string(vcard_string):
    """
    vcard_string: str() or unicode()
    returns VCard()
    """
    vcard = vobject.readOne(vcard_string)
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

    def __init__(self, ddict='', *args):

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
        return unicode(self['N'][0][0])

    @property
    def fname(self):
        return unicode(self['FN'][0][0])

    def alt_keys(self):
        keylist = self.keys()
        for one in ['FN', 'N', 'VERSION']:
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
                line = key + types + ': ' + value[0]
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

    def edit(self):
        """proper edit"""

        def buttons():
            def save_button_callback(button):
                raise SelectedButton(exit_token='Save')
            savebutton = urwid.Button('OK', on_press=save_button_callback)

            def cancel_button_callback(button):
                raise SelectedButton(exit_token='Cancel')
            cancelbutton = urwid.Button('Cancel',
                    on_press=cancel_button_callback)
            return urwid.GridFlow([savebutton, cancelbutton],
                    10, 7, 1, 'center')

        fieldwidgets = []
        for prop in self:
            label = urwid.Text(prop.prop)
            value = urwid.Edit('', prop.value)
            editwidget = urwid.Columns([('fixed', 8, label),
                                        ('flow', value)])

            fieldwidgets.append(urwid.Padding(editwidget, ('fixed left', 3),
                                                          ('fixed right', 3)))

        fieldwidgets.append(buttons())
        listwalker = urwid.SimpleListWalker(fieldwidgets)
        listbox = urwid.ListBox(listwalker)
        header = urwid.Text('Please edit your contacts')
        frame = urwid.Frame(listbox, header=header)
        try:
            urwid.MainLoop(frame, None).run()
        except SelectedButton as sel:
            print(sel.exit_token)

    def edit_name(self):
        """editing the name attributes (N and FN)
        BruteForce Style
        """
        print(self.fname)
        name_split = self.name.split(';')
        name = list()
        name.append(raw_input('Surname (was: ' + name_split[0] + '):'))
        name.append(raw_input('Given name (was: ' + name_split[1] + '):'))
        name.append(raw_input('Additional name (was: ' + name_split[2] + '):'))
        name.append(raw_input('Prefixes (was: ' + name_split[3] + '):'))
        name.append(raw_input('Postfixes (was: ' + name_split[4] + '):'))
        self.fname = raw_input('Displayed name (was: ' + self.fname + '):')
        self.name = ';'.join(name)
        self.edited = 1


class PcQuery(object):
    """Querying the addressbook database"""

    def __init__(self, db_path="~/.pycard/abook.db",
                 encoding="utf-8", errors="strict", debug=False):
        self.db_path = path.expanduser(db_path)
        self.encoding = encoding
        self.errors = errors
        self.debug = debug
        self.display_all = False
        self.print_function = "print_contact_info"
        self._make_tables()
        self._check_table_version()

    def search(self, search_string):
        """returns list of ids from db matching search_string"""
        stuple = ('%' + search_string + '%', )
        sql_s = 'SELECT href FROM vcardtable WHERE vcard LIKE (?)'
        result = self.sql_ex(sql_s, stuple)
        return [row[0] for row in result]

    @property
    def changed(self):
        stuple = (CHANGED, )
        sql_s = 'SELECT href FROM vcardtable WHERE status == (?)'
        result = self.sql_ex(sql_s, stuple)
        return [row[0] for row in result]

    def select_entry(self, search_string):
        """select a single entry from a list matching the search_string

        returns: href
        return type: string
        """
        ids = self.get_contact_id_from_string(search_string)
        if len(ids) > 1:
            print("There are several cards matching your search string:")
            for i, j in enumerate(ids):
                contact = VCard(j, self.db_path)
                print((i + 1), contact.fname)
            while True:  # should break if input not convertible to int
                id_to_edit = raw_input("Which one do you want to edit: ")
                #try:
                id_to_edit = int(id_to_edit)
                if (id_to_edit > 0) and (id_to_edit <= len(ids)):
                    # FIXME what's wrong here again?
                    href_to_edit = ids[id_to_edit - 1][0]
                    break
                #except:
                #    pass
                print("Please only type a number between 1 and", len(ids))
        elif len(ids) != 0:
            href_to_edit = ids[0][0]
        elif len(ids) == 0:
            sys.exit("No matching entry found.")
        print("")
        card_to_edit = VCard(href_to_edit, self.db_path)
        card_to_edit.print_contact_info()
        print("")
        return card_to_edit

    def select_entry_urwid(self, search_string):
        """interactive href selector (urwid based)

        returns: href
        return type: string
        """
        names = self.get_names_vref_from_db(search_string)
        if len(names) is 1:
            return names[0][1]
        if names == list():
            return None
        name_list = list()
        for one in names:
            name_list.append(SelText(one[0], one[1]))
        palette = [('header', 'white', 'black'),
            ('reveal focus', 'black', 'dark cyan', 'standout'), ]
        content = urwid.SimpleListWalker([
            urwid.AttrMap(w, None, 'reveal focus') for w in name_list])

        listbox = urwid.ListBox(content)
        show_key = urwid.Text(u"", wrap='clip')
        head = urwid.AttrMap(show_key, 'header')
        top = urwid.Frame(listbox, head)

        def show_all_input(input, raw):
            """used for urwid test
            to be removed
            """
            show_key.set_text(u"Pressed: " + u" ".join([
                unicode(i) for i in input]))
            return input

        def keystroke(input):
            """used for urwid test
            to be removed
            """
            if input == 'q':
                raise urwid.ExitMainLoop()
            if input is 'enter':
                listbox.get_focus()[0].original_widget
                raise Selected()

        loop = urwid.MainLoop(top, palette,
            input_filter=show_all_input, unhandled_input=keystroke)
        try:
            loop.run()
        except Selected:
            return names[listbox.get_focus()[1]][1]

    def _check_table_version(self):
        """
        tests for curent db Version
        if the table is still empty, insert db_version
        """
        database_version = 7  # the current db VERSION
        #try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT version FROM version')
        result = cursor.fetchone()
        if result == None:
            stuple = (database_version, )  # database version db Version
            cursor.execute('INSERT INTO version (version) VALUES (?)', stuple)
            conn.commit()
        elif not result[0] == database_version:
            sys.exit(str(self.db_path) + " is probably not a valid or an "
                "outdated database.\nYou should consider to remove it and "
                "sync again using pycardsyncer.\n")
        #except Exception as error:
        #    sys.stderr.write('Failed to connect to database,"
        #            "Unknown Error: ' + str(error)+"\n")

    def _make_tables(self):
        """creates tables, also checks existing tables for version number"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''CREATE TABLE version ( version INTEGER )''')
            logging.debug("created version table")
        except sqlite3.OperationalError as detail:
            logging.debug("%s", detail)
        except Exception as error:
            sys.stderr.write('Failed to connect to database,'
                'Unknown Error: ' + str(error) + "\n")
        conn.commit()

        try:
            cursor.execute('''CREATE TABLE vcardtable (
                    href TEXT,
                    etag TEXT,
                    name TEXT,
                    fname TEXT,
                    vcard TEXT,
                    status INT NOT NULL
                    )''')
            logging.debug("created vcardtable table")
        except sqlite3.OperationalError as detail:
            logging.debug("%s", detail)
        except Exception as error:
            sys.stderr.write('Failed to connect to database,'
                'Unknown Error: ' + str(error) + "\n")
        conn.commit()

    def sql_ex(self, statement, stuple=''):
        """wrapper for sql statements, does a "fetchall" """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(statement, stuple)
        result = cursor.fetchall()
        conn.commit()
        cursor.close()
        return result

    def needs_update(self, href, etag=''):
        """checks if we need to update this vcard

        :param href: href of vcard
        :type href: str()
        :param etag: etag of vcard
        :type etag: str()
        :return: True or False
        """
        stuple = (href,)
        sql_s = 'SELECT etag FROM vcardtable WHERE href=(?)'
        result = self.sql_ex(sql_s, stuple)

        if len(result) is 0:
            return True
        elif etag != result[0][0]:
            return True
        else:
            return False

    def update(self, vcard, href='', etag='', status=OK):
        if isinstance(vcard, (str, unicode)):
            vcard = vcard_from_string(vcard)

        if self.href_exists(href):  # existing card
            vcard_s = vcard.serialize()
            stuple = (etag, vcard.name, vcard.fname, vcard_s, status, href)
            sql_s = 'UPDATE vcardtable SET etag = ?, name = ?, fname = ?, \
                 vcard = ?, status = ? WHERE href = ?;'
            self.sql_ex(sql_s, stuple)

        else:
            if href == '':
                for _ in range(10):
                    href = get_random_href()
                    if self.href_exists(href) is False:
                        break
                    # could not find a (random) href that's not yet in the db
                    # broken random number generator?
                    #TODO: what's happens now? exception?
            vcard_s = vcard.serialize()
            stuple = (href, etag, vcard.name, vcard.fname, vcard_s, status)
            sql_s = 'INSERT INTO vcardtable (href, etag, name, fname, vcard, status) \
                VALUES (?,?,?,?,?,?);'
            self.sql_ex(sql_s, stuple)

    def update_href(self, old_href, new_href, etag='', status=OK):
        stuple = (new_href, etag, status, old_href)
        sql_s = 'UPDATE vcardtable SET href = ?, etag = ?, status = ? \
             WHERE href = ?;'
        self.sql_ex(sql_s, stuple)

    def href_exists(self, href):
        sql_s = 'SELECT href FROM vcardtable WHERE href = ?; '
        if len(self.sql_ex(sql_s, (href, ))) == 0:
            return False
        else:
            return True

    def get_etag(self, href):
        """get etag for href

        type href: str()
        return: etag
        rtype: str()
        """
        sql_s = 'SELECT etag FROM vcardtable WHERE href=(?);'
        etag = self.sql_ex(sql_s, (href,))[0][0]
        return etag

    def delete_vcard_from_db(self, vref):
        """
        removes the whole vcard,
        from the property and vcardtable table
        returns nothing
        """
        stuple = (vref, )
        if self.debug:
            print("locally deleting ", vref)
        self.sql_ex('DELETE FROM vcardtable WHERE href=(?)', stuple)

    def get_all_vref_from_db(self):
        """returns a list with all vrefs"""
        result = self.sql_ex('SELECT href FROM vcardtable')
        return [row[0] for row in result]

    def get_names_vref_from_db(self, searchstring=None):
        """
        :return: list of tuples(name, vref) of all entries from the db
        """
        if searchstring is None:
            return self.sql_ex('SELECT fname, href FROM vcardtable ORDER BY name')
        else:
            hrefs = self.get_contact_id_from_string(searchstring)
            temp = list()
            for href in hrefs:
                try:
                    sql_s = 'SELECT fname, href FROM vcardtable WHERE href =(?)'
                    result = self.sql_ex(sql_s, (href, ))
                    temp.append(result[0])
                except IndexError as error:
                    print(href)
                    print(error)
            return temp

    def get_vcard_from_db(self, href):
        """returns a VCard()"""
        sql_s = 'SELECT vcard FROM vcardtable WHERE href=(?)'
        result = self.sql_ex(sql_s, (href, ))
        vcard = VCard(ast.literal_eval(result[0][0]))
        return vcard

    def get_changed(self):
        """returns list of hrefs of locally edited vcards"""
        sql_s = 'SELECT href FROM vcardtable WHERE status == (?)'
        result = self.sql_ex(sql_s, (CHANGED, ))
        return [row[0] for row in result]

    def get_new(self):
        """returns list of hrefs of locally added vcards"""
        sql_s = 'SELECT href FROM vcardtable WHERE status == (?)'
        result = self.sql_ex(sql_s, (NEW, ))
        return [row[0] for row in result]

    def get_marked_delete(self):
        """returns list of tuples (hrefs, etags) of locally deleted vcards"""
        sql_s = 'SELECT href FROM vcardtable WHERE status == (?)'
        result = self.sql_ex(sql_s, (DELETED, ))
        return [row[0] for row in result]

    def mark_delete(self, href):
        """marks the entry as to be deleted on server on next sync"""
        sql_s = 'UPDATE vcardtable SET STATUS = ? WHERE href = ?'
        self.sql_ex(sql_s, (DELETED, href, ))

    def reset_flag(self, href):
        """
        resets the edited flag for a given href to 0 (=not edited locally)
        """
        sql_s = 'UPDATE vcardtable SET edited = 0 WHERE href = ?'
        self.sql_ex(sql_s, (href, ))


def signal_handler(signal, frame):
    """
    tries to hide some ugly python backtraces from the user after
    pressing ctrl-c
    """
    sys.exit(0)


def smartencode(string):
    """convert everything to utf-8"""
    return unicode(string).encode("utf-8", "strict")


def get_random_href():
    """returns a random href"""
    import random
    tmp_list = list()
    for _ in xrange(3):
        rand_number = random.randint(0, 0x100000000)
        tmp_list.append("{0:x}".format(rand_number))
    return "-".join(tmp_list).upper()
