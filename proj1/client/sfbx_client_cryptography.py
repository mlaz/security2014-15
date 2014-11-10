from twisted.internet import defer, reactor
from twisted.web.server import NOT_DONE_YET

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto import Random

from base64 import b64encode, b64decode
from pprint import pprint


#
# SafeBox client crypography utilities API:
# Provides facilities and utilities for preforming cryptographic operations
# on files and identification processes.
#

# class ClientIdentity:
# This class provides a facility for managing the application's cryptographic identity
# and preforming cryptographic operations on given data.
class ClientIdentity(object):

    def __init__(self, dir_name, password, server_key):
        file = open(dir_name + "/private.pem", 'r')
        self.priv_key = RSA.importKey(file.read(), password)
        file.close()

        file = open(dir_name + "/public.pem", 'r')
        self.pub_key = RSA.importKey(file.read(), password)
        file.close()

        self.server_key = RSA.importKey(server_key)

        self.signer = PKCS1_v1_5.new(self.priv_key)
        self.verifier = PKCS1_v1_5.new(self.pub_key)

        self.rnd = Random.new()

    def encryptData(self, data, key=None):
        if key is None:
            key = self.server_key
        return key.encrypt(data, self.rnd.read) #TODO: Be sure about this!

    def decryptData(self, data, key=None):
        if key is None:
            key = self.priv_key
        return key.decrypt(data)

    def signData(self, data):
        hash = SHA256.new(data)
        return self.signer.sign(hash)

    def verifySignature(self, signature, data, key=None):
        if key is None:
            key = self.pub_key
        hash = SHA256.new(data)
        return self.verifier.verify(hash, signature)


# Some utilities:
#

# getTicket Protocol:
class getTicket(Protocol):
    def __init__(self, finished, ci): #TODO: change all calls, add ci
        self.finished = finished
        self.ci = ci
        self.total_response = ""

    def dataReceived(self, bytes):
        self.total_response += bytes

    def connectionLost(self, reason):
        finalTicket = formatTicket(self.total_response)
        self.finished.callback(finalTicket)

    def formatTicket(response):
        response = json.loads(response, object_hook=_decode_dict)
        if (response["status"] == ["error"]):
            print(response["error"])
        else:
            s = response["ticket"]
            print "Encrypted Ticket: ", s
            cryTicket = cr_ticket(str(s))
            print "Decrypted Ticket: ", cryTicket
            return cryTicket

    def cr_ticket(ticket):
        dci = self.ci.decryptData(b64decode(ticket))
        sci = self.ci.signData(dci)
        eci = self.ci.encryptData(sci)
        enc = self.b64encode(eci[0])
        return enc
