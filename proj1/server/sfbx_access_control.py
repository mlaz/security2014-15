from twisted.internet import defer, reactor
from twisted.web.server import NOT_DONE_YET

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto import Random

#from base64 import b64encode, b64decode
from pprint import pprint
from base64 import b64encode, b64decode
import json

from  sfbx_storage import SafeBoxStorage, strip_text

TICKET_TIMEOUT = 3
TICKET_SIZE = 172 # size of signed ticket


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
        #self.verifier = PKCS1_v1_5.new(self.pub_key)

        self.rnd = Random.new()

    #TODO: let's base64 encode and decode here instead of doing it elsewhere
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
        cli_key = RSA.importKey(cli_key)
        enc_ticket = self.server.encryptData(ticket , cli_key)
        timeout = reactor.callLater(TICKET_TIMEOUT * 60, removeTicket_cb, pboxid)
        self.active_tickets.update({pboxid: {'ticket': ticket,  'timeout': timeout}})
        return b64encode(enc_ticket[0])

    #validateTicket: ticket must be base64 encoded
    def validateTicket(self,signature, pboxid, cli_key):
        if pboxid in self.active_tickets.keys():
            self.active_tickets[pboxid]['timeout'].cancel()
            original = self.active_tickets[pboxid]['ticket']
            del self.active_tickets[pboxid]

        cli_key = RSA.importKey(cli_key)
        print signature
        signature = self.server.decryptData(b64decode(signature))#TEST THIS!
        return self.server.verifySignature(signature, original, cli_key)


# class AccessCtrlHandler:
# This class provides a facility for validation of access permissions and client identity,
# which is done when handling every http request received.
class AccessCtrlHandler(object):

    def __init__(self, keys_dirname=0, password=0):
       self.server = ServerIdentity(keys_dirname, password)
       self.ticket_manager = TicketManager(self.server)
       self.storage = SafeBoxStorage()

    # Handling Session resource related operations:
    #

    def handleGetKey(self):
        key = self.server.pub_key.exportKey('PEM')
        print key
        reply_dict = { 'status': "OK", 'key': key }
        return json.dumps(reply_dict, sort_keys=True, encoding="utf-8")

    # handleGetTicket: Checks if the userd ccid exists in the database,
    # if it does returns a ticket.
    def handleGetTicket(self, request):

        def getTicket_cb(data):
            if not data:
                reply_dict = { 'status': {'error': "Invalid Request",
                                          'message': 'User does not exist.'} }
            else:
                pboxid = data[0][0]
                pubkey = data[0][1]
                print pubkey

                ticket = self.ticket_manager.generateTicket(pboxid, pubkey)
                reply_dict = { 'status': "OK", 'ticket': ticket}

            request.write( json.dumps(reply_dict, sort_keys=True, encoding="utf-8") )
            request.finish()

        d = self.storage.getClientData(request)
        d.addCallback(getTicket_cb)
        return NOT_DONE_YET

    # handleValidation: handles the validation process for a given method
    # only calls method if the provided ticket is valid.
    def handleValidation(self, request, method, ticket=None):
        # ticket will only exist from arguments when this method
        # is being called to validate data transfer operations
        if not ticket:
            ticket = request.content.read(TICKET_SIZE)
            print str(ticket)
            if not ticket:
                reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "No ticket on request body."} }
                return json.dumps(reply_dict, encoding="utf-8")


        def handleValidation_cb(data):
            if not data:
                reply_dict = { 'status': {'error': "Invalid Request",
                                          'message': 'User does not exist.'} }

            else:
                pboxid = data[0][0]
                pubkey = data[0][1]
                print pubkey

                if self.ticket_manager.validateTicket(ticket, pboxid, pubkey):
                    print "Valid Ticket!"
                    d = method(request, pboxid)
                    return NOT_DONE_YET

                else:
                    print "Invalid Ticket!"
                    reply_dict = { 'status': {'error': "Invalid Ticket",
                                          'message': 'N/A'} }

            request.write( json.dumps(reply_dict, sort_keys=True, encoding="utf-8") )
            request.finish()

        d = self.storage.getClientData(request)
        d.addCallback(handleValidation_cb)
        return NOT_DONE_YET

    # Handling PBoxes resource related operations:
    #

    #handle ListPBoxes
    def handleListPBoxes(self, request):
        return self.handleValidation(request, self.storage.listPBoxes)

    def handleGetPBoxMData(self, request):
        return self.handleValidation(request, self.storage.getPBoxMData)

    # handleRegisterPBox: Checks if client exists, if so returns error, else registers the client.
    def handleRegisterPBox(self, request):
        # Checking if the client exists.
        # pprint(request.__dict__)
        def checkClientExists_cb(data, key_txt):
            if data:
                reply_dict = { 'status': {'error': "Invalid Request",
                                          'message': 'User already exists.'} }
                request.write( json.dumps(reply_dict, sort_keys=True, encoding="utf-8") )
                request.finish()
            else:
                d = self.storage.registerPBox(request, key_txt)
                return NOT_DONE_YET

        # Validating key.
        key_txt = request.content.read()
        if not key_txt:
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "No key on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")

        cli_key = RSA.importKey(key_txt)
        if not cli_key.can_encrypt():
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "No key on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")

        d = self.storage.getClientData(request)
        d.addCallback(checkClientExists_cb, key_txt)
        return NOT_DONE_YET

    # Handling Files resource related operations:
    #
    def handleListFiles(self, request):
        return self.handleValidation(request, self.storage.listFiles)

    def handleGetFileMData(self, request):
        return self.handleValidation(request, self.storage.getFileMData)

    def handleGetFile(self, request):
        return self.handleValidation(request, self.storage.getFile)

    def handlePutFile(self, request):#
        return self.handleValidation(request, self.storage.putFile)

    def handleUpdateFile(self, request):#
        return self.handleValidation(request, self.storage.updateFile)

    def handleDeleteFile(self, request):
        return self.handleValidation(request, self.storage.deleteFile)

    # Handling Share resource related operations:
    #
