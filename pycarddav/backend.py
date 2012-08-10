#!/usr/bin/env python
# vim: set ts=4 sw=4 expandtab sts=4:
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <geier@lostpackets.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return Christian Geier
# ----------------------------------------------------------------------------
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
        ids = self.search(search_string)
        if len(ids) > 1:
            print("There are several cards matching your search string:")
            for i, j in enumerate(ids):
                contact = model.VCard(j, self.db_path)
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
        card_to_edit = model.VCard(href_to_edit, self.db_path)
        card_to_edit.print_contact_info()
        print("")
        return card_to_edit

    def select_entry2(self, search_string):
        """interactive href selector (urwid based)

        returns: href
        return type: string
        """
        return self.get_names_vref_from_db(search_string)

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
        resets the edited flag for a given href to 0 (=not edited locally)
        """
        sql_s = 'UPDATE vcardtable SET edited = 0 WHERE href = ?'
        self.sql_ex(sql_s, (href, ))


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
