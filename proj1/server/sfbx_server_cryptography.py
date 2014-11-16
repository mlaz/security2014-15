from twisted.internet import defer, reactor

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto import Random

from base64 import b64encode, b64decode
from pprint import pprint

TICKET_TIMEOUT = 3
TICKET_SIZE = 172 # size of signed ticket

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

    #TODO: let's base64 encode and decode here instead of doing it elsewhere
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

# class TicketManager:
# This class provides a facility generating and validating tickets which will be signed
# by the client and sent back to the server inside a request body. A ticket is only valid
# for a single request and lasts for <TICKET_TIMEOUT> minutes.
class TicketManager(object):

    def __init__(self, identity):
        self.server = identity
        self.active_tickets = {}

    #generateTicket: returns base64 encoded ticket
    def generateTicket(self, pboxid, cli_key):
        def removeTicket_cb(pboxid):
            del self.active_tickets[pboxid]

        if pboxid in self.active_tickets.keys():
            self.active_tickets[pboxid]['timeout'].cancel()
            del self.active_tickets[pboxid]

        ticket = str(Random.get_random_bytes(64))
#        pprint(ticket)
#        print type(ticket)
        #cli_key = RSA.importKey(cli_key)
        enc_ticket = self.server.encryptData(ticket , cli_key)
        timeout = reactor.callLater(TICKET_TIMEOUT * 60, removeTicket_cb, pboxid)
        self.active_tickets.update({pboxid: {'ticket': ticket,  'timeout': timeout}})
        return enc_ticket

    #validateTicket: ticket must be base64 encoded
    def validateTicket(self,signature, pboxid, cli_key):
        original = ""
        if pboxid in self.active_tickets.keys():
            self.active_tickets[pboxid]['timeout'].cancel()
            original = self.active_tickets[pboxid]['ticket']
            del self.active_tickets[pboxid]

        cli_key = RSA.importKey(cli_key)
        print signature
        signature = self.server.decryptData(signature)#TEST THIS!
        return self.server.verifySignature(signature, original, cli_key)
