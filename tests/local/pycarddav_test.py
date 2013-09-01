# vim: set fileencoding=utf-8 :
"""these test should test code defined in pycarddav/__init__.py (mainly
the configuration parsing)"""
import os.path
import sys

from pycarddav import ConfigurationParser
from pycarddav import SyncConfigurationParser

# some helper functions

def get_basename():
    """find the base path so we can build proper paths, needed so we can start
    the tests from anywhere"""
    curdir = os.path.basename(os.path.abspath(os.path.curdir))
    if os.path.isdir('tests') and curdir == 'pycarddav':
        basepath = 'tests/'
    elif os.path.isdir('assets') and curdir == 'tests':
        basepath = './'
    elif os.path.isdir('pycarddav') and curdir == 'pycarddav':
        basepath = 'pycarddav/tests/'
    elif curdir == 'local':
        basepath = '../'
    else:
        raise Exception("don't know where I'm")
    return basepath

basepath = get_basename()



def test_basic_config():
    """testing the basic configuration parser
    this rather complicated setup is needed, since py2.6 and py2.7 return
    the accounts list in different orders"""
    sys.argv = ['pycardsyncer', '-c',
                '{0}/assets/configs/base.conf'.format(basepath)]
    conf_parser = ConfigurationParser('let\'s do a test', check_accounts=False)
    conf = conf_parser.parse()

    assert conf.debug == False
    assert conf.sqlite.path == '/home/testman/.pycard/abook.db'
    assert conf.filename.endswith('tests//assets/configs/base.conf') == True
    def assert_work(accounts_conf):
        assert accounts_conf.write_support == False
        assert accounts_conf.resource == 'http://test.com/abook/collection'
        assert accounts_conf.name == 'work'
        assert accounts_conf.passwd == 'foobar'
        assert accounts_conf.verify == False
        assert accounts_conf.auth == 'basic'
        assert accounts_conf.user == 'testman'

    def assert_davical(accounts_conf):
        assert accounts_conf.write_support == True
        assert accounts_conf.resource == 'https://carddavcentral.com:4443/caldav.php/tester/abook/'
        assert accounts_conf.name == 'davical'
        assert accounts_conf.passwd == 'barfoo23'
        assert accounts_conf.verify == '/home/testman/.pycard/cacert.pem'
        assert accounts_conf.auth == 'digest'
        assert accounts_conf.user == 'tester'

    count = 0
    for one in conf.accounts:
        if one.name == 'work':
            assert_work(one)
            count += 1
        elif one.name == 'davical':
            assert_davical(one)
            count += 1
        elif one.name == 'work_no_verify':
            assert one.verify == True
            count += 1
        else:
            assert True == 'this should not be reached'
    assert count == 3


def test_basic_debug():
    """testing the basic configuration parser"""
    sys.argv = ['pycardsyncer', '-c',
                '{0}/assets/configs/base.conf'.format(basepath),
                '--debug']
    conf_parser = ConfigurationParser('let\'s do a test', check_accounts=False)
    conf = conf_parser.parse()
    assert conf.debug == True
    assert conf.sqlite.path == '/home/testman/.pycard/abook.db'
    assert conf.filename.endswith('tests//assets/configs/base.conf') == True
    def assert_work(accounts_conf):
        assert accounts_conf.write_support == False
        assert accounts_conf.resource == 'http://test.com/abook/collection'
        assert accounts_conf.name == 'work'
        assert accounts_conf.passwd == 'foobar'
        assert accounts_conf.verify == False
        assert accounts_conf.auth == 'basic'
        assert accounts_conf.user == 'testman'

    def assert_davical(accounts_conf):
        assert accounts_conf.write_support == True
        assert accounts_conf.resource == 'https://carddavcentral.com:4443/caldav.php/tester/abook/'
        assert accounts_conf.name == 'davical'
        assert accounts_conf.passwd == 'barfoo23'
        assert accounts_conf.verify == '/home/testman/.pycard/cacert.pem'
        assert accounts_conf.auth == 'digest'
        assert accounts_conf.user == 'tester'

    count = 0
    for one in conf.accounts:
        if one.name == 'work':
            assert_work(one)
            count += 1
        elif one.name == 'davical':
            assert_davical(one)
            count += 1
        elif one.name == 'work_no_verify':
            assert one.verify == True
            count += 1
        else:
            assert True == 'this should not be reached'
    assert count == 3


def test_sync_conf_parser():
    """testing the basic configuration parser"""
    sys.argv = ['pycardsyncer', '-c',
                '{0}/assets/configs/base.conf'.format(basepath),
                '-a', 'work',]
    conf_parser = SyncConfigurationParser()
    conf = conf_parser.parse()
    assert conf.debug == False
    assert conf.sqlite.path == '/home/testman/.pycard/abook.db'
    assert conf.filename.endswith('tests//assets/configs/base.conf') == True
    assert conf.sync.accounts == set(['work'])
    def assert_work(accounts_conf):
        assert accounts_conf.write_support == False
        assert accounts_conf.resource == 'http://test.com/abook/collection/'
        assert accounts_conf.name == 'work'
        assert accounts_conf.passwd == 'foobar'
        assert accounts_conf.verify == False
        assert accounts_conf.auth == 'basic'
        assert accounts_conf.user == 'testman'

    def assert_davical(accounts_conf):
        assert accounts_conf.write_support == True
        assert accounts_conf.resource == 'https://carddavcentral.com:4443/caldav.php/tester/abook/'
        assert accounts_conf.name == 'davical'
        assert accounts_conf.passwd == 'barfoo23'
        assert accounts_conf.verify == '/home/testman/.pycard/cacert.pem'
        assert accounts_conf.auth == 'digest'
        assert accounts_conf.user == 'tester'

    count = 0
    for one in conf.accounts:
        if one.name == 'work':
            assert_work(one)
            count += 1
        elif one.name == 'davical':
            assert_davical(one)
            count += 1
        elif one.name == 'work_no_verify':
            assert one.verify == True
            count += 1
        else:
            assert True == 'this should not be reached'
    assert count == 3
