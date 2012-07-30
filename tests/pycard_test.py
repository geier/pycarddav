# vim: set fileencoding=utf-8 :
import pycarddav.pycard

vcard1 = """BEGIN:VCARD
VERSION:3.0
N:Gödel;François
FN:François Gödel
TEL;TYPE=WORK,VOICE:+49-123-678901
TEL;TYPE=HOME,VOICE:(101) 1234 4123
ADR;TYPE=WORK:;;Essalág 100;Torshavn;50800;Færøerne
EMAIL;TYPE=PREF,INTERNET:francois@goedel.net
END:VCARD
"""

vcard1_vcf = """BEGIN:VCARD
VERSION:3.0
FN:François Gödel
N:Gödel;François;;;
ADR;TYPE=WORK:;;Essalág 100;Torshavn;50800;Færøerne;
EMAIL;TYPE=PREF,INTERNET:francois@goedel.net
TEL;TYPE=WORK,VOICE:+49-123-678901
TEL;TYPE=HOME,VOICE:(101) 1234 4123
END:VCARD"""


def get_vcard1():
    return pycarddav.pycard.vcard_from_string(vcard1)

def test_serialize_to_vcf():
    assert get_vcard1().vcf.encode('utf-8') == vcard1_vcf
