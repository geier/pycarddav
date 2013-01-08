# vim: set fileencoding=utf-8 :
import vagrant
import pytest
import pycarddav.carddav as carddav

HANZ_BASE = 'http://localhost:8080/davical/caldav.php/hanz/addresses/'
LENNA_BASE = 'http://localhost:8080/davical/caldav.php/lenna/addresses/'


def test_url_does_not_exist():
    vbox = vagrant.Vagrant()
    vbox.up()
    with pytest.raises(carddav.requests.exceptions.HTTPError):
        carddav.PyCardDAV('http://localhost:8080/doesnotexist/')


def test_no_auth():
    vbox = vagrant.Vagrant()
    vbox.up()
    with pytest.raises(Exception):
        carddav.PyCardDAV(HANZ_BASE)


def test_basic_auth():
    vbox = vagrant.Vagrant()
    vbox.up()
    syncer = carddav.PyCardDAV(LENNA_BASE, user='lenna', passwd='test')
    abook = syncer.get_abook()
    assert abook == dict()
