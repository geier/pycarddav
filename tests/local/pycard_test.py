# vim: set fileencoding=utf-8 :
import pycarddav.model
import pycarddav.backend as backend
import os.path
import pytest
import random


# some helper functions

def get_basename():
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


def get_vcard(cardname):
    """gets a vcard from the assets directory"""
    filename = basepath + 'assets/' + cardname + '.vcf'
    with file(filename) as vcard:
            cardstring = vcard.read()
    return pycarddav.model.vcard_from_string(cardstring)


def get_output(function_name):
    with file(basepath + 'local/output/' + function_name + '.out') as output_file:
        output = output_file.readlines()
    return ''.join(output).strip('\n')

# \helper functions


def pytest_funcarg__emptydb(request):
    mydb = backend.SQLiteDb(db_path=':memory:')
    mydb.check_account_table('test', 'http://test.com')
    return mydb

## tests


def test_serialize_to_vcf():
    random.seed(1)
    assert get_vcard('gödel').vcf.encode('utf-8') == get_output('serialize_to_vcf')


def test_broken_nobegin():
    with pytest.raises(Exception) as error:
        get_vcard('broken_nobegin')
        print error

def test_db_init(emptydb):
    assert emptydb._dump('test') == list()


def test_vcard_insert1(emptydb):
    random.seed(1)
    emptydb.check_account_table('test', 'http://test.com')
    emptydb.update(get_vcard('gödel').vcf, 'test', href='/something.vcf')
    assert str(emptydb._dump('test')) == get_output('vcard_insert1')


def test_vcard_insert_with_status(emptydb):
    random.seed(1)
    emptydb.check_account_table('test', 'http://test.com')
    emptydb.update(get_vcard('gödel').vcf,
                   'test',
                   href='/something.vcf',
                   status=backend.NEW)
    assert str(emptydb._dump('test')) == get_output('vcard_insert_with_status')
