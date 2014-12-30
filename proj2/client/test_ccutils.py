import cc_utils as a
from M2Crypto import X509

print "Extracting the certificate list"
c = a.getCertList()
print "The list: ", c
print "The first certificate: ", c[0]
# The function as_text() is available so that the certificate is more "human-friendly"
# print c[0].as_text()
print "Getting the public key from that certificate"
k = c[0].get_pubkey()
print "The certificate's public key: ", k


print "Testing the sign and verify functions"
s = "string de teste - seguranca 2014/15"
st = a.sign(s)
print st

v = a.verify(s, st)
print v
