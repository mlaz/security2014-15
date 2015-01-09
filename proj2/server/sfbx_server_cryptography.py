from twisted.internet import defer, reactor

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256, HMAC
from Crypto import Random

from base64 import b64encode, b64decode
from pprint import pprint


# class ServerIdentity:
# This class provides a facility for managing the application's cryptographic identity
# and preforming cryptographic operations on given data.
class ServerIdentity(object):

    def __init__(self, dir_name, password):
        file = open(dir_name + "/private.pem", 'r')
        self.priv_key = RSA.importKey(file.read(), password)
        file.close()

        file = open(dir_name + "/public.pem", 'r')
        self.pub_key = RSA.importKey(file.read(), password)
        file.close()

        self.signer = PKCS1_v1_5.new(self.priv_key)
        #self.verifier = PKCS1_v1_5.new(self.pub_key)

        self.rnd = Random.new()

    def encryptData(self, data, key=None):
        if key is None:
            key = self.pub_key
        else:
            key = RSA.importKey(key)
        return b64encode(key.encrypt(data, self.rnd.read)[0]) #TODO: Be sure about this!

    def decryptData(self, data, key=None):
        if key is None:
            key = self.priv_key
        else:
            key = RSA.importKey(key)
        return key.decrypt(b64decode(data))

    def signData(self, data):
        hash = SHA256.new(data)
        return self.signer.sign(hash)

    def verifySignature(self, signature, data, key=None):
        if key is None:
            print  "KEY NONE!"
            key = self.pub_key
        verifier = PKCS1_v1_5.new(key)
        hash = SHA256.new(data)
        return verifier.verify(hash, str(signature))

    def genHash(self, passwd, salt=None):
        if not salt:
            salt = Random.get_random_bytes(SHA256.digest_size)
            #print "generated salt: ", salt
        #print "hashing passwd: ", passwd
        hash = HMAC.new(salt, digestmod=SHA256)
        hash.update(str(passwd))
        return (b64encode(hash.hexdigest()), self.encryptData(salt))

