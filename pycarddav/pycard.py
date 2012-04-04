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


"""
Database Layout
===============

current version number: 5
tables: version, vcardtable, properties, blobproperties

version:
    version (INT): only one line: current db version

vcardtable:
    href (TEXT PRIMARY KEY)
    etag (TEXT)
    name (TEXT): name as in vcard, seperated by ';'
    fname (TEXT): formated name
    version (TEXT): vcard version
    edited (INT): status of this card
        * 0: not touched since last sync
        * 1: properties edited or added (news to be pushed to server)
        * 2: new card, needs to be created on the server

properties:


blobproperties:




"""

try:
    import sys
    from os import path
    import ast
    import urwid
    import sqlite3
    import vobject

    import my_exceptions
except ImportError, error:
    print error
    sys.exit(1)

try:
    from termcolor import cprint

    def print_bold(text):
        """prints text bold"""
        cprint(text, attrs=['bold'])
except ImportError:

    def print_bold(text):
        """prints text bold"""
        print(text)


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


class MessageException(Exception):
    """
    this is used for breaking out of urwid's main loop
    and "returning" a string, this is probably not at all how it is supposed to
    work. But it works (tm).
    """
    pass


NO_STRINGS = [u"n", "n", u"no", "no"]
YES_STRINGS = [u"y", "y", u"yes", "yes"]


class VCard(list):
    """
    internal representation of a VCard. This is mainly a list with some
    associated methods, each list element is a CardProperty
    h_ref: unique id (really just the url) of the VCard
    db_path: database file from which to initialize the VCard
    """

    def __init__(self, h_ref="", db_path=""):
        self.h_ref = h_ref
        self.db_path = db_path
        self.edited = 0
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        stuple = (h_ref, )
        cur.execute('SELECT name, fname, version FROM vcardtable WHERE href=(?)', stuple)
        result = cur.fetchall()
        self.name = result[0][0]
        self.fname = result[0][1]

        cur.execute('SELECT * FROM properties WHERE href=(?)', stuple)
        result = cur.fetchall()
        for (vcard_id, vcard_property, vcard_value,
            vcard_href, param_dict) in result:
            self.append(CardProperty(vcard_property,
                        vcard_value,
                        ast.literal_eval(param_dict), vcard_id), )
        conn.close()

    def get_prop(self, card_property):
        """
        returns a list of all CardProperties matching "card_property",
        making VCard work like a dict (and perhaps it better would be one)
        """
        collector = list()
        for prop in self:
            if prop.prop == card_property:
                collector.append(prop)
        return collector

    def get_props(self):
        """
        returns a list of all properties (each property only once,
        even if it occurs multiple times) this vcard has
        """
        collector = list()
        for prop in self:
            collector.append(prop.prop)
        return list(set(collector))

    def print_contact_info(self, display_all=False):
        """new style contact card information printing"""
        print_bold(unicode("Name: " + self.fname).encode("utf-8"))
        for prop in ("EMAIL", "TEL", ):
            for line in self.get_prop(prop):
                line.print_yourself()
        if display_all == True:
            for props in self.get_props():
                if not props in ("EMAIL", "TEL",):
                    for line in self.get_prop(props):
                        line.print_yourself()

    def print_email(self):
        """prints only name, email and type for use with mutt"""
        for email in self.get_prop('EMAIL'):
            print unicode(email.value + u"\t" + self.fname + u"\t"
                          + email.type_list()).encode("utf-8")

    def edit(self):
        """proper edit"""
        while True:
            print ""
            number = 0
            print '{:>3}'.format(number), "NAME", ":", self.fname
            for line in self:
                number = number + 1
                print '{:>3}'.format(number), line.prop, '(', \
                    line.type_list(), ')', ":", line.value
            input_string = raw_input("Edit ('n' for adding a property, "
                "'e' number for editing the property number, "
                "'d' number for deleting property number, 's' for saving): ")
            if input_string[0:2] in ["e ", u"e "]:
                id_to_edit = int(input_string[2:])
                if id_to_edit == 0:
                    self.edit_name()
                else:
                    self[id_to_edit - 1].edit()
            if input_string in ["s", u"s"]:
                break
            if input_string in ['q', u'q']:
                sys.exit()
            if input_string in ['n']:
                self.add_prop()

    def edit_name(self):
        """editing the name attributes (N and FN)
        BruteForce Style
        """
        print self.fname
        name_split = self.name.split(';')
        name = list()
        name.append( raw_input('Surname (was: ' + name_split[0] + '):') )
        name.append(raw_input('Given name (was: ' + name_split[1] + '):') )
        name.append(raw_input('Surname (was: ' + name_split[2] + '):') )
        name.append(raw_input('Surname (was: ' + name_split[3] + '):') )
        self.fname = raw_input('Displayed Name (was: ' + self.fname + '):')
        self.name = ';'.join(name)
        self.edited = 1

    def add_prop(self):
        """add a new property"""
        prop = raw_input("Property Name: ")
        value = raw_input("Value: ")
        types = raw_input("Types: ")
        if prop in ['']:
            return
        params_d = dict()
        if not types == unicode():
            params_d[u'TYPE'] = types.split(',')
        self.append(CardProperty(prop, value, params_d, edited=2))

    def save(self):
        """saves the changed properties to the db"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for prop in self:
            if prop.edited == 1:  # updated property
                stuple = (unicode(prop.prop), unicode(prop.value),
                          unicode(self.h_ref), unicode(prop.params),
                          unicode(prop.uid))
                cursor.execute('UPDATE properties SET property = ? ,'
                                'value = ?, href = ?, parameters = ? '
                                'WHERE id = ?;', stuple)
            if prop.edited == 2:  # new property
                prop.params = u'{}'
                stuple = (unicode(prop.prop), unicode(prop.value),
                          unicode(self.h_ref), unicode(prop.params),)
                cursor.execute('INSERT INTO properties (property ,'
                                'value, href, parameters) VALUES '
                                '(?, ?, ?, ?);', stuple)
        conn.commit()
        if self.edited == 1:  # name & fname edited
            stuple = (self.fname, self.name, self.h_ref)
            cursor.execute('UPDATE vcardtable SET fname = ? , '
                           'name = ? WHERE href = ?;', stuple)
        cursor.execute('UPDATE vcardtable SET edited = 1 WHERE href = ?',
                       (self.h_ref, ))
        conn.commit()
        conn.close()
        print "Saved your edits to the local db." \
              "They are NOT yet on the server."


class CardProperty(list):
    """
    A CardProperty object holds one VCard property including all parameters
    self.prop = the name of the property; type: unicode
    self.value = the value of the property; type: unicode
    self.params = all associated parameters; type: dict
    """

    def __init__(self, prop, value, params, uid=0, edited=0):
        self.prop = prop
        self.value = value
        self.params = params
        self.uid = uid
        self.edited = edited

    def type_list(self):
        """returns all types parameters, separated by "," """
        try:
            params = u', '.join(self.params[u'TYPE'])
        except TypeError:
            params = u''
        except KeyError:
            params = u''
        return params

    def edit(self):
        """edits this card property"""
        temp = raw_input(smartencode(self.prop + u' [' + self.value + u']: '))
        if not temp == unicode():
            self.value = temp
            self.edited = 1
        temp = raw_input(smartencode(u"Types [" + self.type_list() + u"]: "))
        if not temp == unicode():
            self.params[u'TYPE'] = temp.split(',')
            self.edited = 1

    def print_yourself(self):
        """
        prints the cardproperty,
        couldn't get __str__ to work, becaus of too many \n
        """
        if self.value != unicode():
            if self.params == dict():
                print unicode(self.prop.capitalize() + u": "
                              + self.value).encode("utf-8")
            else:
                print unicode(self.prop.capitalize() + " ("
                              + self.type_list() + u"): "
                              + self.value).encode("utf-8")


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
        """
        first we get the list of contact_ids matching the search string
        then these are printed using the different print functions
        """
        contact_ids = self.get_contact_id_from_string(search_string)
        while len(contact_ids) != 0:
            contact_id = contact_ids.pop()
            if self.print_function == "print_email":
                VCard(contact_id, self.db_path).print_email()
            else:
                VCard(contact_id, self.db_path).print_contact_info(
                        self.display_all)
                if len(contact_ids) > 0:
                    print ""

    def get_contact_id_from_string(self, search_string):
        """returns list of ids from db matching search_string"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = ('%' + search_string + '%', )
        cursor.execute('SELECT href FROM properties WHERE value LIKE (?)',
                stuple)
        result = cursor.fetchall()
        cursor.execute('SELECT href FROM vcardtable WHERE name LIKE (?)',
                stuple)
        result.extend(cursor.fetchall())
        result = list(set(result))
        conn.close()
        return [row[0] for row in result]

    def select_entry(self, search_string):
        """select a single entry from a list matching the search_string"""
        ids = self.get_contact_id_from_string(search_string)
        if len(ids) > 1:
            print "There are several cards matching your search string:"
            for i, j in enumerate(ids):
                contact = VCard(j, self.db_path)
                print (i + 1), contact.fname
            while True:  # should break if input not convertible to int
                id_to_edit = raw_input("Which one do you want to edit: ")
                #try:
                id_to_edit = int(id_to_edit)
                if (id_to_edit > 0) and (id_to_edit <= len(ids)):  # FIXME what's wrong here again?
                    href_to_edit = ids[id_to_edit - 1][0]
                    break
                #except:
                #    pass
                print "Please only type a number between 1 and", len(ids)
        elif len(ids) != 0:
            href_to_edit = ids[0][0]
        elif len(ids) == 0:
            sys.exit("No matching entry found.")
        print ""
        card_to_edit = VCard(href_to_edit, self.db_path)
        card_to_edit.print_contact_info()
        print ""
        #while (edit != "y") and (edit != "N") and (edit != ""):
            #edit = raw_input("Is this the entry you want to edit [y/N]? ")
        #if (edit == u"N") or (edit == ""):
            #sys.exit()
        #else:
        return card_to_edit

    def select_entry_urwid(self, search_string):
        """interactive href seleter (urwid based)"""
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
                focus = listbox.get_focus()[0].original_widget
                #sys.exit(focus.href)
                raise my_exceptions.MessageException(focus.href)

        loop = urwid.MainLoop(top, palette,
            input_filter=show_all_input, unhandled_input=keystroke)
        try:
            loop.run()
        except my_exceptions.MessageException as error:
            return str(error)

    def _check_table_version(self):
        """
        tests for curent db Version
        if the table is still empty, insert db_version
        """
        database_version = 5  # the current db VERSION
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
        #except Exception, error:
        #    sys.stderr.write('Failed to connect to database,"
        #            "Unknown Error: ' + str(error)+"\n")

    def _make_tables(self):
        """creates tables, also checks existing tables for version number"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''CREATE TABLE version ( version INTEGER )''')
            if self.debug:
                print "created version table"
        except sqlite3.OperationalError as detail:
            if self.debug:
                print detail
        except Exception, error:
            sys.stderr.write('Failed to connect to database,'
                'Unknown Error: ' + str(error) + "\n")
        conn.commit()

        try:
            cursor.execute('''CREATE TABLE vcardtable (
                    href TEXT PRIMARY KEY NOT NULL,
                    etag TEXT,
                    name TEXT,
                    fname TEXT,
                    version TEXT,
                    edited INT
                    )''')
            if self.debug:
                print "created vcardtable"
        except sqlite3.OperationalError as detail:
            if self.debug:
                print detail
        except Exception, error:
            sys.stderr.write('Failed to connect to database,'
                'Unknown Error: ' + str(error) + "\n")
        conn.commit()
        # properties table
        try:
            cursor.execute('''CREATE TABLE properties (
            id INTEGER PRIMARY KEY NOT NULL,
            property TEXT NOT NULL,
            value TEXT,
            href TEXT NOT NULL,
            parameters TEXT,
            FOREIGN KEY(href) REFERENCES vcardtable(href)
            )''')
            if self.debug:
                print "created properties table"
        except sqlite3.OperationalError as detail:
            if self.debug:
                print detail
        except Exception, error:
            sys.stderr.write('Failed to connect to database,'
                'Unknown Error: ' + str(error) + "\n")
        conn.commit()
        # create blob table
        try:
            cursor.execute('''CREATE TABLE blobproperties (
            id INTEGER PRIMARY KEY NOT NULL,
            property TEXT NOT NULL,
            value TEXT,
            href TEXT NOT NULL,
            parameters TEXT,
            FOREIGN KEY(href) REFERENCES vcardtable(href)
            )''')
            if self.debug:
                print "created blobproperties table"
        except sqlite3.OperationalError as detail:
            if self.debug:
                print detail
        except Exception, error:
            sys.stderr.write('Failed to connect to database,'
                'Unknown Error: ' + str(error) + "\n")
        conn.commit()
        cursor.close()

    def check_new_etag(self, vref, v_etag):
        """returns True when the etag has been updated, otherwise False

        :param vref: vref
        :type vref: str
        :param v_etag: etag
        :type v_etag: str
        :rtype: bool, True when etags do not match, otherwise False
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (vref, )
        cursor.execute('SELECT etag FROM vcardtable WHERE href=(?);', stuple)
        if v_etag == cursor.fetchall()[0][0]:
            return_code = False
        else:
            return_code = True
        conn.commit()
        cursor.close()
        return return_code

    def check_vref_exists(self, vref):
        """
        returns False if vref already exists in db
        returns True otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (vref, )
        cursor.execute('SELECT count(*) FROM vcardtable WHERE href=(?);',
                        stuple)
        if cursor.fetchall() == [(1, )]:
            return_code = False
        else:
            return_code = True
        conn.commit()
        cursor.close()
        return return_code

    def insert_vref(self, vref, new=0):
        """
        inserts vref into the vcardtable
        returns nothing
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (vref, new,)
        cursor.execute('INSERT INTO vcardtable (href, edited)'
                       'VALUES (?, ?);', stuple)
        conn.commit()
        cursor.close()

    def update_name(self, vref, fname, name, version='3.0'):
        """ updates the name field in the vcardtable

        :parameter fname: formatted name
        :type fname: unicode()
        :parameter name: name property as in vcard (seperated by ';')
        :type name: unicode()
        :return: nothing
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (fname, name, version, vref )
        cursor.execute('UPDATE vcardtable SET fname=(?), name=(?), '
                       'version=(?) WHERE href=(?);', stuple)
        conn.commit()
        cursor.close()

    def update_etag(self, vref, v_etag):
        """returns nothing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (v_etag, vref)
        cursor.execute('UPDATE vcardtable SET etag=(?) WHERE href=(?);',
                       stuple)
        conn.commit()
        cursor.close()

    def update_vref(self, old_vref, new_vref):
        """
        updates vref
        returns: nothing
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (new_vref, old_vref)
        cursor.execute('UPDATE vcardtable SET href=(?) WHERE href=(?);',
                        stuple)
        cursor.execute('UPDATE properties SET href=(?) WHERE href=(?);',
                       stuple)
        conn.commit()
        cursor.close()

    def delete_vcard_props_from_db(self, vref):
        """
        does NOT actually remove the whole vcard, only the lines
        from the property table
        returns nothing
        """
        # FIXME this should also reset the etag
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (vref, )
        cursor.execute('DELETE FROM properties WHERE href=(?)', stuple)
        cursor.execute('DELETE FROM blobproperties WHERE href=(?)', stuple)
        conn.commit()
        cursor.close()

    def delete_vcard_from_db(self, vref):
        """
        removes the whole vcard,
        from the property and vcardtable table
        returns nothing
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (vref, )
        if self.debug:
            print "locally deleting ", vref
        cursor.execute('DELETE FROM properties WHERE href=(?)', stuple)
        conn.commit()
        cursor.execute('DELETE FROM vcardtable WHERE href=(?)', stuple)
        conn.commit()
        cursor.close()

    def get_all_vref_from_db(self):
        """returns a list with all vrefs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT href FROM vcardtable')
        result = cursor.fetchall()
        return [row[0] for row in result]

    def get_names_vref_from_db(self, searchstring=None):
        """
        :return: list of tuples(name, vref) of all entries from the db
        """
        if searchstring is None:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT fname, href FROM vcardtable ORDER BY name')
            result = cursor.fetchall()
            return result
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            hrefs = self.get_contact_id_from_string(searchstring)

            temp = list()
            for href in hrefs:
                try:
                    stuple = (href,)
                    cursor.execute(
                        'SELECT fname, href FROM vcardtable WHERE href =(?)',
                         stuple)
                    temp.append(cursor.fetchall()[0])
                except IndexError as error:
                    print href
                    print error
            return temp

    def get_vcard_from_db(self, vref):
        """returns a vobject.vCard()"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (vref, )
        cursor.execute('SELECT id, property, value, parameters FROM properties'
                        ' WHERE href=(?)', stuple)
        result = cursor.fetchall()

        card = vobject.vCard()
        #import ipdb; ipdb.set_trace()
        for uid, prop, value, parameters in result:
            # atm we need to treat N and ADR properties differently 
            # FIXME: ORG should be treated differently, too
            tmp = card.add(prop)
            if prop == u'N':
                name = value.split(';')
                tmp.value = vobject.vcard.Name(family=name[0],
                                               given=name[1],
                                               additional=name[2],
                                               prefix=name[3],
                                               suffix=name[4])
            elif prop == u'ADR':
                adr = value.split(';')
                tmp.value = vobject.vcard.Address(street=adr[0],
                                                  city=adr[1],
                                                  region=adr[2],
                                                  code=adr[3],
                                                  country=adr[4],
                                                  box=adr[5],
                                                  extended=adr[6])
            #PROPFUCK
            elif prop in [u'CATEGORIES', u'NICKNAMES']:
                cats = value.split(',')
                tmp.value = cats
            else:
                tmp.value = value
            tmp.params = ast.literal_eval(parameters)
        cursor.execute('SELECT id, property, value, parameters '
                       'FROM blobproperties WHERE href=(?)', stuple)
        result = cursor.fetchall()
        for uid, prop, value, parameters in result:
            tmp = card.add(prop)
            tmp.value = str(value)
            tmp.params = ast.literal_eval(parameters)
        conn.close()
        #import ipdb; ipdb.set_trace()
        return card

    def get_local_edited_hrefs(self):
        """returns list of hrefs of locally edited vcards"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT href FROM vcardtable where edited == 1')
        result = cursor.fetchall()
        return [row[0] for row in result]

    def get_local_new_hrefs(self):
        """returns list of hrefs of locally added vcards"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT href FROM vcardtable where edited == 2')
        result = cursor.fetchall()
        return [row[0] for row in result]

    def insert_vcard_in_db(self, vref, vcard):
        """
        vref: ref to remote vcf file
        vcard: vobject.Vcard()
        returns nothing
        """
        if vcard.name == "VCARD":

            name = vcard.n.value.family + u';' \
                 + vcard.n.value.given + u';' \
                 + vcard.n.value.additional + u';' \
                 + vcard.n.value.prefix + u';' \
                 + vcard.n.value.suffix
            fname = vcard.fn.value
            version = vcard.version.value
            for line in vcard.getChildren():
                # this might break, was tried/excepted before
                line.transformFromNative()

                property_name = line.name
                property_value = line.value

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                try:
                    if line.ENCODING_paramlist == [u'b']:
                        print "found binary"
                        stuple = (unicode(property_name),
                                  sqlite3.Binary(property_value),
                                  vref, unicode(line.params),)
                        cursor.execute('INSERT INTO blobproperties '
                                '(property, value, href, parameters) '
                                'VALUES (?,?,?,?);', stuple)
                        conn.commit()

                except AttributeError:
                    if property_name in [u'FN', u'N', u'VERSION']:
                        continue
                    if type(property_value) == list:
                        property_value = (',').join(property_value)
                    stuple = (unicode(property_name), property_value,
                              vref, unicode(line.params),)
                    cursor.execute('INSERT INTO properties '
                                   '(property, value, href, parameters) '
                                   'VALUES (?,?,?,?);', stuple)
                    cursor.close()
                    conn.commit()
            self.update_name(vref, fname, name, version=version)
        else:
            return -1  # this is not a vcard

    def reset_flag(self, href):
        """
        resets the edited flag for a given href to 0 (=not edited locally)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stuple = (href, )

        cursor.execute('UPDATE vcardtable SET edited = 0 WHERE href = ?',
                       stuple)
        conn.commit()
        conn.close()


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
