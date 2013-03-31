# vim: set fileencoding=utf-8 :
"""these test should test code defined in pycarddav/__init__.py (mainly
the configuration parsing)"""
import os.path
import sys

from pycarddav import ConfigurationParser

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
    """testing the basic configuration parser"""
    sys.argv = ['pycardsyncer', '-c',
                '{0}/assets/configs/base.conf'.format(basepath)]
    conf_parser = ConfigurationParser('let\'s do a test', check_accounts=False)
    conf = conf_parser.parse()

    assert conf.debug == False
    assert conf.sqlite.path == '/home/testman/.pycard/abook.db'
    assert conf.accounts[0].write_support == ''
    assert conf.accounts[0].resource == 'http://test.com/abook/collection'
    assert conf.accounts[0].name == 'work'
    assert conf.accounts[0].passwd == ''
    assert conf.accounts[0].verify == False
    assert conf.accounts[0].auth == 'basic'
    assert conf.accounts[0].user == 'testman'
    assert conf.accounts[1].write_support == True
    assert conf.accounts[1].resource == 'https://carddavcentral.com:4443/caldav.php/tester/abook/'
    assert conf.accounts[1].name == 'davical'
    assert conf.accounts[1].passwd == ''
    assert conf.accounts[1].verify == '/home/testman/.pycard/cacert.pem'
    assert conf.accounts[1].auth == 'digest'
    assert conf.accounts[1].user == 'tester'
    assert conf.filename.endswith('tests//assets/configs/base.conf') == True

def test_basic_debug():
    """testing the basic configuration parser with debug True"""
    sys.argv = ['pycardsyncer', '-c',
                '{0}/assets/configs/base.conf'.format(basepath),
                '--debug']
    conf_parser = ConfigurationParser('let\'s do a test', check_accounts=False)
    conf = conf_parser.parse()

    assert conf.debug == True
    assert conf.sqlite.path == '/home/testman/.pycard/abook.db'
    assert conf.accounts[0].write_support == ''
    assert conf.accounts[0].resource == 'http://test.com/abook/collection'
    assert conf.accounts[0].name == 'work'
    assert conf.accounts[0].passwd == ''
    assert conf.accounts[0].verify == False
    assert conf.accounts[0].auth == 'basic'
    assert conf.accounts[0].user == 'testman'
    assert conf.accounts[1].write_support == True
    assert conf.accounts[1].resource == 'https://carddavcentral.com:4443/caldav.php/tester/abook/'
    assert conf.accounts[1].name == 'davical'
    assert conf.accounts[1].passwd == ''
    assert conf.accounts[1].verify == '/home/testman/.pycard/cacert.pem'
    assert conf.accounts[1].auth == 'digest'
    assert conf.accounts[1].user == 'tester'
    assert conf.filename.endswith('tests//assets/configs/base.conf') == True
