from twisted.internet import reactor

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto import Random

from base64 import b64encode, b64decode
from pprint import pprint
import json
from  sfbx_storage import SafeBoxStorage, strip_text

TICKET_TIMEOUT = 3

#
# SafeBox server access control utilities API:
# Provides facilities and utilities for preforming access control related operations
#

# Some utilities:
#

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
        self.verifier = PKCS1_v1_5.new(self.pub_key)

        self.rnd = Random.new()

    def encryptData(self, data, key=None):
        if key is None:
            key = self.pub_key
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

# class TicketManager:
# This class provides a facility generating and validating tickets which will be signed
# by the client and sent back to the server inside a request body. A ticket is only valid
# for a single request and lasts for <TICKET_TIMEOUT> minutes.
class TicketManager(object):

    def __init__(self, identity):
        self.server = identity
        self.active_tickets = {}

    #generateTicket:
    def generateTicket(self, pboxid, cli_key):
        def removeTicket_cb(pboxid):
            del self.active_tickets[pboxid]

        if pboxid in self.active_tickets.keys():
            self.active_tickets[pboxid]['timeout'].cancel()
            del self.active_tickets[pboxid]

        ticket = str(Random.get_random_bytes(64))
#        pprint(ticket)
#        print type(ticket)
        enc_ticket = self.server.encryptData(ticket , self.server.pub_key)
        timeout = reactor.callLater(TICKET_TIMEOUT * 60, removeTicket_cb, pboxid)
        self.active_tickets.update({pboxid: {'ticket': ticket,  'timeout': timeout}})
        return enc_ticket

    #validateTicket:
    def validateTicket(self, signature, pboxid, cli_key):
        if pboxid in self.active_tickets.keys():
            self.active_tickets[pboxid]['timeout'].cancel()
            ticket = self.active_tickets[pboxid]['ticket']
            del self.active_tickets[pboxid]

        signature = self.server.decryptData(signature)
        return self.server.verifySignature(signature, ticket, cli_key)


# class AccessCtrlHandler:
# This class provides a facility for validation of access permissions and client identity,
# which is done when handling every http request received.
class AccessCtrlHandler(object):

    def __init__(self, keys_dirname=0, password=0):
       self.server = ServerIdentity(keys_dirname, password)
#       self.ticket_manager = TicketManager(self.server)
       self.storage = SafeBoxStorage()

    # Handling Session resource related operations:
    #

    def handleGetKey(self):
        key = self.server.pub_key.exportKey('PEM')
        print key
        reply_dict = { 'status': "OK", 'list': key }
        return json.dumps(reply_dict, sort_keys=True, encoding="utf-8")

    # def handleGetTicket(request):
        
    #     token = 
    #     reply_dict = { 'status': "OK", 'ticket': ticket}
    #     return json.dumps(reply_dict, sort_keys=True, encoding="utf-8")
    #     return

    # Handling PBoxes resource related operations:
    #

    def handleListPBoxes(self, request):
        return self.storage.listPBoxes(request)

    def handleGetPBoxMData(self, request):
        return self.storage.getPBoxMData(request)

    def handleRegisterPBox(self, request):
        return self.storage.registerPBox(request)

    # Handling Files resource related operations:
    #

    def handleListFiles(self, request):
        return self.storage.listFiles(request)

    def handleGetFile(self, request):
        return self.storage.getFile(request)

    def handlePutFile(self, request):
        return self.storage.putFile(request)

    def handleUpdateFile(self, request):
        return self.storage.updateFile(request)

    def handleDeleteFile(self, request):
        return self.storage.deleteFile(request)

    # Handling Share resource related operations:
    #
