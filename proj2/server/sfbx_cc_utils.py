import M2Crypto
import PyKCS11
from M2Crypto import X509
from base64 import b64encode

PKCS11_LIB = "/usr/local/lib/libpteidpkcs11.so"
ASN1_UTF8_FLGS = 0x10 #ASN1_STRFLGS_UTF8_CONVERT
CERT_LABEL = "CITIZEN AUTHENTICATION CERTIFICATE"
SUBCA_LABEL = "AUTHENTICATION SUB CA"
KEY_LABEL = "CITIZEN AUTHENTICATION KEY"

ecraiz_cert = "certificates/ECRaizEstado.crt"
cc_cert1 = "certificates/Cartao de Cidadao 001.cer"
cc_cert2 = "certificates/Cartao de Cidadao 002.cer"


# Returns an M2Crypto.X509.X509 certicicate foa given label (CKA_LABEL).
# The card availability check could be improved here.
# (Let's not use hardcoded PIN codes, so we don't void cards.)
# def get_certificate(label, pin):
#     pkcs11 = PyKCS11.PyKCS11Lib()
#     pkcs11.load(PKCS11_LIB)
#     slots = pkcs11.getSlotList()
#     session = pkcs11.openSession(slots[0])

#     try:
#         session.login(pin)
#     except:
#         return None

#     objs = session.findObjects( template=(
#         (PyKCS11.CKA_LABEL, label),
#         (PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE)) )

#     der = ''.join(chr(c) for c in objs[0].to_dict()['CKA_VALUE'])
#     return X509.load_cert_string(der, X509.FORMAT_DER)

# Returns the certificate subject's commonName and serialNumber (aka ccid) for a given cert string.
def get_subjdata_from_cert_str(cert_str):
    cert = X509.load_cert_string(cert_str)
    subj = cert.get_subject()
    cn_entry = subj.get_entries_by_nid(subj.nid['commonName'])
    sn_entry = subj.get_entries_by_nid(subj.nid['serialNumber'])
    common_name = cn_entry[0].get_data().as_text(flags=ASN1_UTF8_FLGS)
    serial_number = sn_entry[0].get_data().as_text(flags=ASN1_UTF8_FLGS)
    return (common_name, serial_number[2:])

def validate_cert(cert_str, subca_str):
    cert = X509.load_cert_string(cert_str)
    sub_ca = X509.load_cert_string(subca_str)
    ecraiz = X509.load_cert(ecraiz_cert)

    if "001" not in sub_ca.get_issuer().as_text():
        cccert = X509.load_cert(cc_cert2, format=0)
    else:
        cccert = X509.load_cert(cc_cert1, format=0)

    if sub_ca.get_subject().as_text() == cert.get_issuer().as_text():
        pkey = sub_ca.get_pubkey()
        if not cert.verify(pkey):
            return False
        elif cccert.get_subject().as_text() == sub_ca.get_issuer().as_text():
            pkey = cccert.get_pubkey()
            if not sub_ca.verify(pkey):
                return False
            elif ecraiz.get_subject().as_text() == cccert.get_issuer().as_text():
                pkey = ecraiz.get_pubkey()
                if cccert.verify(pkey):
                    if ecraiz.verify(pkey):
                        return True

    return False
