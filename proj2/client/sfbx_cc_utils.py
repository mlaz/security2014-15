import M2Crypto
import PyKCS11
from M2Crypto import X509
from base64 import b64encode

PKCS11_LIB = "/usr/local/lib/libpteidpkcs11.so"
ASN1_UTF8_FLGS = 0x10 #ASN1_STRFLGS_UTF8_CONVERT
CERT_LABEL = "CITIZEN AUTHENTICATION CERTIFICATE"
SUBCA_LABEL = "AUTHENTICATION SUB CA"
KEY_LABEL = "CITIZEN AUTHENTICATION KEY"

# Returns an M2Crypto.X509.X509 certicicate foa given label (CKA_LABEL).
# The card availability check could be improved here.
# (Let's not use hardcoded PIN codes, so we don't void cards.)
def get_certificate(label, pin):
    pkcs11 = PyKCS11.PyKCS11Lib()
    pkcs11.load(PKCS11_LIB)
    try:
        slots = pkcs11.getSlotList()
    except:
        return None

    try:
        session = pkcs11.openSession(slots[0])
    except:
        return None

    try:
        session.login(pin)
    except:
        return None

    objs = session.findObjects( template=(
        (PyKCS11.CKA_LABEL, label),
        (PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE)) )

    der = ''.join(chr(c) for c in objs[0].to_dict()['CKA_VALUE'])
    return X509.load_cert_string(der, X509.FORMAT_DER)

# Returns the certificate subject's commonName and serialNumber (aka ccid).
def get_subjdata_from_cert(cert):
    subj = cert.get_subject()
    cn_entry = subj.get_entries_by_nid(subj.nid['commonName'])
    sn_entry = subj.get_entries_by_nid(subj.nid['serialNumber'])
    common_name = cn_entry[0].get_data().as_text(flags=ASN1_UTF8_FLGS)
    serial_number = sn_entry[0].get_data().as_text(flags=ASN1_UTF8_FLGS)
    return (common_name, serial_number)

# Signs given data
def sign(data, label, pin):
    pkcs11 = PyKCS11.PyKCS11Lib()
    pkcs11.load(PKCS11_LIB)
    slots = pkcs11.getSlotList()
    session = pkcs11.openSession(slots[0])
    #print "logging in"
    try:
        session.login(pin)
    except:
        return None

    key = session.findObjects( template=( (PyKCS11.CKA_LABEL, label),
                                          (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
                                          (PyKCS11.CKA_KEY_TYPE, PyKCS11.CKK_RSA) ))[0]
    #print key
    #print "logged in"
    mech = PyKCS11.Mechanism(PyKCS11.CKM_SHA1_RSA_PKCS, "")

    sig = session.sign(key, data, mech)
    ret = ''.join(chr(c) for c in sig)
    #print "ORIGINAL SIGNATURE: " + ret
    return ret
