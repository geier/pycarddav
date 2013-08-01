#!/usr/bin/env python2
# vim: set fileencoding=utf-8 :
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

import argparse
import ConfigParser
import getpass
import re
import logging
import os
import signal
import sys
import xdg.BaseDirectory

import version

from netrc import netrc
from urlparse import urlsplit

__productname__ = 'pyCardDAV'
__version__ = version.__version__
__author__ = 'Christian Geier'
__copyright__ = 'Copyright 2011-2013 Christian Geier & contributors'
__author_email__ = 'pycarddav@lostpackets.de'
__description__ = 'A CardDAV based address book tool'
__license__ = 'Expat/MIT, see COPYING'
__homepage__ = 'http://lostpackets.de/pycarddav/'


def capture_user_interruption():
    """
    Tries to hide to the user the ugly python backtraces generated by
    pressing Ctrl-C.
    """
    signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))


class Namespace(dict):
    """The pycarddav configuration holder.

    This holder is a dict subclass that exposes its items as attributes.
    Inspired by NameSpace from argparse, Configuration is a simple
    object providing equality by attribute names and values, and a
    representation.

    Warning: Namespace instances do not have direct access to the dict
    methods. But since it is a dict object, it is possible to call
    these methods the following way: dict.get(ns, 'key')

    See http://code.activestate.com/recipes/577887-a-simple-namespace-class/
    """
    def __init__(self, obj=None):
        dict.__init__(self, obj if obj else {})

    def __dir__(self):
        return list(self)

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, dict.__repr__(self))

    def __getattribute__(self, name):
        try:
            return self[name]
        except KeyError:
            msg = "'%s' object has no attribute '%s'"
            raise AttributeError(msg % (type(self).__name__, name))

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]


class Section(object):

    READERS = { bool: ConfigParser.SafeConfigParser.getboolean,
                float: ConfigParser.SafeConfigParser.getfloat,
                int: ConfigParser.SafeConfigParser.getint,
                str: ConfigParser.SafeConfigParser.get }

    def __init__(self, parser, group):
        self._parser = parser
        self._group = group
        self._schema = None
        self._parsed = {}

    def matches(self, name):
        return self._group == name.lower()

    def is_collection(self):
        return False

    def parse(self, section):
        if self._schema is None:
            return None

        for option, default, filter_ in self._schema:
            try:
                if filter_ is None:
                    reader = ConfigParser.SafeConfigParser.get
                    filter_ = lambda x: x
                else:
                    reader = Section.READERS[type(default)]
                self._parsed[option] = filter_(reader(self._parser, section, option))

                # Remove option once handled (see the check function).
                self._parser.remove_option(section, option)
            except ConfigParser.Error:
                self._parsed[option] = default

        return Namespace(self._parsed)

    @property
    def group(self):
        return self._group

    def _parse_bool_string(self, value):
        """if value is either 'True' or 'False' it returns that value as a bool,
        otherwise it returns the value"""
        value = value.strip().lower()
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            return os.path.expanduser(value)

    def _parse_write_support(self, value):
        """returns True if value is YesPlease..., this is a rather dirty
        solution, but it works fine (TM)"""
        value = value.strip()
        if value == 'YesPleaseIDoHaveABackupOfMyData':
            return True
        else:
            return False

class AccountSection(Section):
    def __init__(self, parser):
        Section.__init__(self, parser, 'accounts')
        self._schema = [
            ('user', '', None),
            ('passwd', '', None),
            ('resource', '', None),
            ('auth', 'basic', None),
            ('verify', True, self._parse_bool_string),
            ('write_support', '', self._parse_write_support),
        ]

    def is_collection(self):
        return True

    def matches(self, name):
        match = re.match('account (?P<name>.*)', name, re.I)
        if match:
            self._parsed['name'] = match.group('name')
        return match is not None


class SQLiteSection(Section):
    def __init__(self, parser):
        Section.__init__(self, parser, 'sqlite')
        self._schema = [
            ('path', ConfigurationParser.DEFAULT_DB_PATH, os.path.expanduser),
        ]


class ConfigurationParser(object):
    """A Configuration setup tool.

    This object takes care of command line parsing as well as
    configuration loading. It also prepares logging and updates its
    output level using the debug flag read from the command-line or
    the configuration file.
    """
    DEFAULT_DB_PATH = xdg.BaseDirectory.save_data_path('pycard') + 'abook.db'
    DEFAULT_PATH = "pycard"
    DEFAULT_FILE = "pycard.conf"

    def __init__(self, desc, check_accounts=True):
        # Set the configuration current schema.
        self._sections = [ AccountSection, SQLiteSection ]

        # Build parsers and set common options.
        self._check_accounts = check_accounts
        self._conf_parser = ConfigParser.SafeConfigParser()
        self._arg_parser = argparse.ArgumentParser(
            description=desc, version=__version__)
        self._arg_parser.add_argument(
            "-c", "--config", action="store", dest="filename",
            default=self._get_default_configuration_file(), metavar="FILE",
            help="an alternate configuration file")
        self._arg_parser.add_argument(
            "--debug", action="store_true", dest="debug", help="enables debugging")

    def parse(self):
        """Start parsing.

        Once the commandline parser is eventually configured with specific
        options, this function must be called to start parsing. It first
        parses the command line, and then the configuration file.

        If parsing is successful, the function check is then called.
        When check is a success, the Configuration instance is
        returned. On any error, None is returned.
        """
        args = self._read_command_line()

        # Prepare the logger with the level read from command line.
        logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

        if not args.filename:
            logging.error('Could not find configuration file')
            return None
        try:
            if not self._conf_parser.read(os.path.expanduser(args.filename)):
                logging.error('Cannot read %s', args.filename)
                return None
            else:
                logging.debug('Using configuration from %s', args.filename)
        except ConfigParser.Error, e:
            logging.error("Could not parse %s: %s", args.filename, e)
            return None

        conf = self._read_configuration(args)

        # Update the logger using the definitive output level.
        logging.getLogger().setLevel(logging.DEBUG if conf.debug else logging.INFO)

        return conf if self.check(conf) else None

    def check(self, ns):
        """Check the configuration before returning it from parsing.

        This default implementation warns the user of the remaining
        options found in the configuration file. It then checks the
        validity of the common configuration values. It returns True
        on success, False otherwise.

        This function can be overriden to augment the checks or the
        configuration tweaks achieved before the parsing function
        returns.
        """
        result = True

        for section in self._conf_parser.sections():
            for option in self._conf_parser.options(section):
                logging.debug("Ignoring %s:%s in configuration file", section, option)

        if self._check_accounts:
            if self.check_property(ns, 'accounts'):
                for account in ns.accounts:
                    result &= self.check_account(account)
            else:
                logging.error("No account found")
                result = False

        return result

    def check_account(self, ns):
        result = True

        if not ns.auth in ['basic', 'digest']:
            logging.error("Value %s is not allowed for in  Account %s:auth",
                          ns.auth, ns.name)
            result = False

        if not self.check_property(ns, 'resource', 'Account %s:resource' % ns.name):
            return False

        if not len(ns.passwd):
            hostname = urlsplit(ns.resource).hostname
            try:
                auths = netrc().authenticators(hostname)
            except IOError:
                auths = False
            if auths:
                if not ns.user or auths[0] == ns.user:
                    logging.debug("Read password for user %s on %s in .netrc",
                                  auths[0], hostname)
                    ns.user = auths[0]
                    ns.passwd = auths[2]
                else:
                    logging.error("User %s not found for %s in .netrc",
                                  ns.user, hostname)
                    result = False
            elif ns.user:
                # Do not ask for password if execution is already doomed.
                if result:
                    prompt = 'CardDAV password (account ' + ns.name + '): '
                    ns.passwd = getpass.getpass(prompt=prompt)
            else:
                logging.error("Missing credentials for %s", hostname)
                result = False

        return result

    def check_property(self, ns, property_, display_name=None):
        names = property_.split('.')
        obj = ns
        try:
            for name in names:
                obj = dict.get(obj, name)
            if not obj:
                raise AttributeError()
        except AttributeError:
            logging.error('Mandatory option %s is missing',
                          display_name if display_name else property_)
            return False

        return True

    def dump(self, conf, intro='Using configuration:', tab=1):
        """Dump the loaded configuration using the logging framework.

        The values displayed here are the exact values which are seen by
        the program, and not the raw values as they are read in the
        configuration file.
        """
        logging.debug(intro)

        for name, value in sorted(dict.copy(conf).iteritems()):
            if type(value) is list:
                for o in value:
                    self.dump(o, '\t'*tab + name + ':', tab + 1)
            elif type(value) is Namespace:
                self.dump(value, '\t'*tab + name + ':', tab + 1)
            elif name != 'passwd':
                logging.debug('%s%s: %s', '\t'*tab, name, value)

    def _read_command_line(self):
        items = {}
        for key, value in vars(self._arg_parser.parse_args()).iteritems():
            if '__' in key:
                section, option = key.split('__')
                items.setdefault(section, Namespace({}))[option] = value
            else:
                items[key] = value
        return Namespace(items)

    def _read_configuration(self, overrides):
        """Build the configuration holder.

        First, data declared in the configuration schema are extracted
        from the configuration file, with type checking and possibly
        through a filter. Then these data are completed or overriden
        using the values read from the command line.
        """
        items = {}
        try:
            if self._conf_parser.getboolean('default', 'debug'):
                overrides['debug'] = True
        except ValueError:
            pass

        for section in self._conf_parser.sections():
            parser = self._get_section_parser(section)
            if not parser is None:
                values = parser.parse(section)
                if parser.is_collection():
                    if not items.has_key(parser.group):
                        items[parser.group] = []
                    items[parser.group].append(values)
                else:
                    items[parser.group] = values

        for key in dir(overrides):
            items[key] = Namespace.get(overrides, key)

        return Namespace(items)

    def _get_section_parser(self, section):
        for cls in self._sections:
            parser = cls(self._conf_parser)
            if parser.matches(section):
                return parser
        return None

    def _get_default_configuration_file(self):
        """Return the configuration filename.

        This function builds the list of paths known by pycarddav and
        then return the first one which exists. The first paths
        searched are the ones described in the XDG Base Directory
        Standard. Each one of this path ends with
        DEFAULT_PATH/DEFAULT_FILE.

        On failure, the path DEFAULT_PATH/DEFAULT_FILE, prefixed with
        a dot, is searched in the home user directory. Ultimately,
        DEFAULT_FILE is searched in the current directory.
        """
        paths = []

        resource = os.path.join(
            ConfigurationParser.DEFAULT_PATH, ConfigurationParser.DEFAULT_FILE)
        paths.extend([os.path.join(path, resource)
            for path in xdg.BaseDirectory.xdg_config_dirs])

        paths.append(os.path.expanduser(os.path.join('~', '.' + resource)))
        paths.append(os.path.expanduser(ConfigurationParser.DEFAULT_FILE))

        for path in paths:
            if os.path.exists(path):
                return path

        return None

class SyncConfigurationParser(ConfigurationParser):
    """A specialized setup tool for synchronization."""
    def __init__(self):
        ConfigurationParser.__init__(self, "syncs the local db to the CardDAV server")

        self._arg_parser.add_argument(
            "-a", "--account", action="append", dest="sync__accounts",
            metavar="NAME", help="use only the NAME account (can be used more than once)")

    def check(self, ns):
        result = ConfigurationParser.check(self, ns)

        accounts = [account.name for account in ns.accounts]

        if ns.sync.accounts:
            for name in set(ns.sync.accounts):
                if not name in [a.name for a in ns.accounts]:
                    logging.warn('Uknown account %s', name)
                    ns.sync.accounts.remove(name)
            if len(ns.sync.accounts) == 0:
                logging.error('No valid account selected')
                result = False
        else:
            ns.sync.accounts = accounts

        for account in ns.accounts:
            if account.resource[-1] != '/':
                account.resource = account.resource + '/'

        ns.sync.accounts = set(ns.sync.accounts)

        return result

