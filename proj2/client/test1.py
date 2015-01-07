from StringIO import StringIO
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Hash import HMAC, SHA256
import sys
import sqlite3
import PAM
import pprint
import cc_utils as a
import sfbx_cc_utils as b
from base64 import b64encode
from sfbx_client_cryptography import *

# CHANGE THIS BEFORE TESTING
pin = None
if pin is None:
	print "You forgot to change the pin to test!"
	sys.exit(0)

# retriving the auth cert and the auth sub ca
# CLIENT SIDE
cert = b.get_certificate(b.CERT_LABEL, pin)
subca = b.get_certificate(b.SUBCA_LABEL, pin)

# checking the trust chain
# certificates must be sent by the client to the server
# SERVER SIDE
#print a.certChain(cert, subca)

# generating a nonce
# SERVER SIDE
data = Random.get_random_bytes(64)
print "Nonce: ", data

# signing with the CC
# CLIENT SIDE
s = b.sign(data, b.KEY_LABEL, pin)
print "signed nonce: ", s

# retriving the key from the cert
# CLIENT SIDE
pkey = cert.get_pubkey()
#print "public key from cert: ", pkey

der = pkey.as_der()
#print "pkey as der: ", der
#print "pkey as der, b64encode: ", der.encode("base64")

rsakey = RSA.importKey(der)
#print "RSA Key: ", rsakey

rsakey2 = RSA.importKey(rsakey.exportKey(format='PEM'))
#print rsakey.exportKey(format='PEM')
#print "RSA Key as PEM: ", rsakey2

# verify the signature
# CLIENT SIDE
pkey.verify_init()
t1 = pkey.verify_update(data)
t2 = pkey.verify_final(s)
if t1 == t2:
	print "Sig verified"

# insert into the DB
# SERVER SIDE
name, bi = b.get_subjdata_from_cert(cert)
userId = bi[2:]
CI = ClientIdentity("111222333", "mypass")
pubkey = CI.pub_key

'''The functions to generate the salt and the
   hash are already implemented in the genHash()
   function on the server side (?)'''
#
salt = Random.get_random_bytes(SHA256.digest_size)
hash = HMAC.new(salt, digestmod=SHA256)
passwd = 'security'
hash.update(passwd)
pwd = hash.hexdigest().encode("base64")
salt = salt.encode("base64")
#
rsakey2 = rsakey.exportKey(format='PEM')
pubkey = pubkey.exportKey(format='PEM')
conn = sqlite3.connect('/media/sf_SECURITY/repo/proj2/server/safebox.sqlite')
conn.text_factory = str
c = conn.cursor()

# print "userId: ", userId
# print "ccKey: \n", rsakey2
# print "pubKey: \n", pubkey
# print "username: ", name
# print "hashed password: ", pwd
# print "salt: ", salt

#rsakey2 = pkey.as_pem(cipher=None)
c.execute("INSERT INTO PBox (UserCCId, UserCCKey, PubKey, UserName, Password, Salt) VALUES (?, ?, ?, ?, ?, ?)", (userId, rsakey2, pubkey, name, pwd, salt))
conn.commit()
c.execute('SELECT * FROM PBox')
data1 = c.fetchone()
#pprint(data1)
c.close()

# using the PAM
# SERVER SIDE (?)
print "datalen:", len(data)
print "signlen:", len(s)
def pam_conv(auth, query_list, userData):

        resp = []

        for i in range(len(query_list)):
                query, type = query_list[i]
                print query
                if query == 'Original:':
                        resp.append((b64encode(data), 0))
                elif query == 'Signature:':
                        resp.append((b64encode(s), 0))
                else:
                        resp.append((pwd, 0))
        return resp

auth = PAM.pam()
auth.start('myservice')
auth.set_item(PAM.PAM_USER, '1')
auth.set_item(PAM.PAM_CONV, pam_conv)
try:
        auth.authenticate()
except PAM.error, resp:
        print 'AUTH FAIL (%s)' % resp
except:
        print 'Internal error'
else:
        print 'SUCCESS!'
