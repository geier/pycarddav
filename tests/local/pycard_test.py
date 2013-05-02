#!/usr/bin/env python2
# vim: set fileencoding=utf-8 :
import pycarddav.model
import os.path
import pytest


def get_basename():
    curdir = os.path.basename(os.path.abspath(os.path.curdir))
    if os.path.isdir('tests') and curdir == 'pycarddav':
        basepath = 'tests/'
    elif os.path.isdir('assets') and curdir == 'tests':
        basepath = './'
    elif os.path.isdir('pycarddav') and curdir == 'pycarddav':
        basepath = 'pycarddav/tests/'
    else:
        raise Exception('Cannot find assets dir')
    return basepath

basepath = get_basename()

vcard1_vcf = """BEGIN:VCARD
VERSION:3.0
FN:François Gödel
N:Gödel;François;;;
ADR;TYPE=WORK:;;Essalág 100;Torshavn;50800;Færøerne;
EMAIL;TYPE=PREF,INTERNET:francois@goedel.net
TEL;TYPE=WORK,VOICE:+49-123-678901
TEL;TYPE=HOME,VOICE:(101) 1234 4123
END:VCARD"""

import pycarddav.backend


def get_vcard(cardname):
    filename = basepath + 'assets/' + cardname + '.vcf'
    with file(filename) as vcard:
            cardstring = vcard.read()
    return pycarddav.model.vcard_from_string(cardstring)


def test_serialize_to_vcf():
    assert get_vcard('gödel').vcf.encode('utf-8') == vcard1_vcf


def test_broken_nobegin():
    with pytest.raises(Exception) as error:
        get_vcard('broken_nobegin')
        print error


def pytest_funcarg__emptydb(request):
    tmpdir = request.getfuncargvalue("tmpdir")
    mydb = pycarddav.backend.SQLiteDb(db_path=tmpdir.strpath + '/abook.db')
    return mydb


def test_db_init(emptydb):
    assert emptydb._dump() == list()


output_vcard_insert1 = [(u'/something.vcf', u'', u'G\xf6del;Fran\xe7ois;;;', u'Fran\xe7ois G\xf6del', u"[(u'ADR', [(u';;Essal\\xe1g 100;Torshavn;50800;F\\xe6r\\xf8erne;', {u'TYPE': [u'WORK']})]), (u'N', [(u'G\\xf6del;Fran\\xe7ois;;;', {})]), (u'VERSION', [(u'3.0', {})]), (u'TEL', [(u'+49-123-678901', {u'TYPE': [u'WORK', u'VOICE']}), (u'(101) 1234 4123', {u'TYPE': [u'HOME', u'VOICE']})]), (u'EMAIL', [(u'francois@goedel.net', {u'TYPE': [u'PREF', u'INTERNET']})]), (u'FN', [(u'Fran\\xe7ois G\\xf6del', {})])]", 0)]


def test_vcard_insert1(emptydb):
    emptydb.update(get_vcard('gödel').vcf, href='/something.vcf')
    assert emptydb._dump() == output_vcard_insert1
