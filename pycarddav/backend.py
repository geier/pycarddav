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
The SQLite backend implementation.

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
    from pycarddav import model
    import sys
    import ast
    import sqlite3
    import logging
    from os import path

except ImportError, error:
    print(error)
    sys.exit(1)


OK = 0
NEW = 1
CHANGED = 2
DELETED = 9


class SQLiteDb(object):
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

    def _dump(self):
        """return vcardtable, used for testing"""
        sql_s = 'SELECT * FROM vcardtable'
        result = self.sql_ex(sql_s)
        return result

    @property
    def changed(self):
        """get list of CHANGED cards"""
        stuple = (CHANGED, )
        sql_s = 'SELECT href FROM vcardtable WHERE status == (?)'
        result = self.sql_ex(sql_s, stuple)
        return [row[0] for row in result]

    def _check_table_version(self):
        """tests for curent db Version
        if the table is still empty, insert db_version
        """
        database_version = 7  # the current db VERSION
        #try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT version FROM version')
        result = cursor.fetchone()
        if result is None:
            stuple = (database_version, )  # database version db Version
            cursor.execute('INSERT INTO version (version) VALUES (?)', stuple)
            conn.commit()
        elif not result[0] == database_version:
            sys.exit(str(self.db_path) +
                     " is probably not a valid or an outdated database.\n"
                     "You should consider to remove it and sync again using "
                     "pycardsyncer.\n")
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
        """insert a new or update an existing card in the db

        :param vcard: vcard to be inserted or updated
        :type vcard: model.VCard()
        :param href: href of the card on the server, if this href already
                     exists in the db the card gets updated. If no href is
                     given, a random href is chosen and it is implied that this
                     card does not yet exist on the server, but will be
                     uploaded there on next sync.
        :type href: str()
        :param etag: the etga of the vcard, if this etag does not match the
                     remote etag on next sync, this card will be updated from
                     the server. For locally created vcards this should not be
                     set
        :type etag: str()
        :param status: status of the vcard
                       * OK: card is in sync with remote server
                       * NEW: card is not yet on the server, this needs to be
                              set for locally created vcards
                       * CHANGED: card locally changed, will be updated on the
                                  server on next sync (if remote card has not
                                  changed since last sync)
                       * DELETED: card locally delete, will also be deleted on
                                  one the server on next sync (if remote card
                                  has not changed)
        :type status: one of backend.OK, backend.NEW, backend.CHANGED,
                      BACKEND.DELETED

        """
        if isinstance(vcard, (str, unicode)):
            vcard = model.vcard_from_string(vcard)

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
            sql_s = ('INSERT INTO vcardtable '
                     '(href, etag, name, fname, vcard, status) '
                     'VALUES (?,?,?,?,?,?);')
            self.sql_ex(sql_s, stuple)

    def update_href(self, old_href, new_href, etag='', status=OK):
        """updates old_href to new_href, can also alter etag and status,
        see update() for an explanation of these parameters"""
        stuple = (new_href, etag, status, old_href)
        sql_s = 'UPDATE vcardtable SET href = ?, etag = ?, status = ? \
             WHERE href = ?;'
        self.sql_ex(sql_s, stuple)

    def href_exists(self, href):
        """returns True if href already exist in db

        :param href: href
        :type href: str()
        :returns: True or False
        """
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

    def get_all_vref_from_db_not_new(self):
        """
        :returns: list of not new vrefs
        """
        sql_s = 'SELECT href FROM vcardtable WHERE STATUS != (?)'
        stuple = (NEW,)
        result = self.sql_ex(sql_s, stuple)
        return [one[0] for one in result]

    def get_names_vref_from_db(self, searchstring=None):
        """
        :return: list of tuples(name, vref) of all entries from the db
        """
        if searchstring is None:
            return self.sql_ex('SELECT fname, href FROM vcardtable '
                               'ORDER BY name')
        else:
            hrefs = self.search(searchstring)
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
        vcard = model.VCard(ast.literal_eval(result[0][0]))
        vcard.href = href
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
        sql_s = 'SELECT href, etag FROM vcardtable WHERE status == (?)'
        result = self.sql_ex(sql_s, (DELETED, ))
        return result

    def mark_delete(self, href):
        """marks the entry as to be deleted on server on next sync"""
        sql_s = 'UPDATE vcardtable SET STATUS = ? WHERE href = ?'
        self.sql_ex(sql_s, (DELETED, href, ))

    def reset_flag(self, href):
        """
        resets the status for a given href to 0 (=not edited locally)
        """
        sql_s = 'UPDATE vcardtable SET status = ? WHERE href = ?'
        self.sql_ex(sql_s, (OK, href, ))


def get_random_href():
    """returns a random href"""
    import random
    tmp_list = list()
    for _ in xrange(3):
        rand_number = random.randint(0, 0x100000000)
        tmp_list.append("{0:x}".format(rand_number))
    return "-".join(tmp_list).upper()
