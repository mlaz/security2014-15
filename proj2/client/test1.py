from StringIO import StringIO
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Hash import HMAC, SHA256
import sqlite3
import cc_utils as a
import sfbx_cc_utils as b
from sfbx_client_cryptography import *

# change this before use
pin = "xxxx"

#label1 = "CITIZEN AUTHENTICATION CERTIFICATE"
#label2 = "AUTHENTICATION SUB CA"

# retriving the auth cert and the auth sub ca
cert = b.get_certificate(b.CERT_LABEL, pin)
subca = b.get_certificate(b.SUBCA_LABEL, pin)

# checking the trust chain
# THIS MUST BE DONE IN THE SERVER
# certificates must be sent by the client to the server
print a.certChain(cert, subca)

# generating a nonce

data = Random.get_random_bytes(64)
print "Nonce: ", data

# signing with the CC

s = b.sign(data, b.KEY_LABEL, pin)
print "signed nonce: ", s

# retriving the key from the cert

pkey = cert.get_pubkey()
print "public key from cert: ", pkey
der = pkey.as_der()
print "pkey as der: ", der
print "pkey as der, b64encode: ", der.encode("base64")
rsakey = RSA.importKey(der)
print "RSA Key: ", rsakey

rsakey2 = RSA.importKey(rsakey.exportKey(format='PEM'))
print rsakey.exportKey(format='PEM')
print "RSA Key as PEM: ", rsakey2

# verify the signature

pkey.verify_init()
t1 = pkey.verify_update(data)
t2 = pkey.verify_final(s.decode("base64"))
if t1 == t2:
	print "Sig verified"

# insert into the DB

name, bi = b.get_subjdata_from_cert(cert)
userId = bi[2:]
CI = ClientIdentity("111222333", "mypass")
pubkey = CI.pub_key

salt = Random.get_random_bytes(SHA256.digest_size)
hash = HMAC.new(salt, digestmod=SHA256)
passwd = 'security'
hash.update(passwd)
pwd = hash.hexdigest().encode("base64")
salt = salt.encode("base64")
rsakey2 = rsakey.exportKey(format='PEM')
pubkey = pubkey.exportKey(format='PEM')
conn = sqlite3.connect('/home/security/Desktop/security2014-p4g4/proj2/server/safebox.sqlite')
conn.text_factory = str
c = conn.cursor()

print "userId: ", userId
print "ccKey: \n", rsakey2
print "pubKey: \n", pubkey
print "username: ", name
print "hashed password: ", pwd
print "salt: ", salt

name_str = StringIO()
print >>name_str, name

c.execute("INSERT INTO PBox (UserCCId, UserCCKey, PubKey, UserName, Password, Salt) VALUES (?, ?, ?, ?, ?, ?)", (userId, rsakey2, pubkey, name, pwd, salt))
conn.commit()
c.execute('SELECT * FROM PBox')
data = c.fetchone()
print(data)
c.close()
