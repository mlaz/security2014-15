from twisted.internet import defer, reactor
from Crypto.Hash import SHA256
from Crypto import Random

from Crypto.PublicKey import RSA

from sfbx_server_cryptography import ServerIdentity

NONCE_TIMEOUT = 3
TICKET_TIMEOUT = 3
TICKET_SIZE = 172 # size of signed ticket


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
        else:
            return False

        cli_key = RSA.importKey(cli_key)
        print signature
        signature = self.server.decryptData(signature)#TEST THIS!
        return self.server.verifySignature(signature, original, cli_key)

# class SessionManager:
# This class provides a facility generating and validating authentication challange nonces
# which will be signed by the client and sent back to the server inside an
# authentication request(startsession and).
# A nonce is only valid for a single request and lasts for <SESSION_TIMEOUT> minutes.
class SessionManager(object):

    def __init__(self, identity):
        self.server = identity
        self.authm = AuthManager(identity)
        self.active_sessions = {}

    def getNonce(self, cli_key):
        return self.authm.generateNonce(cli_key)

    def startSession(self, signature, nonceid, cli_key, pboxid):
        if pboxid in self.active_sessions.keys():
            del self.active_sessions[pboxid]

        if self.authm.validateNonce (signature, nonceid, cli_key):
            timeout = reactor.callLater(NONCE_TIMEOUT * 60, self.killSession_cb, pboxid)
            self.active_sessions.update({pboxid : timeout})
            return True
        else:
            return False

    def hasSession(self, pboxid):
        return pboxid in self.active_sessions.keys()

    def killSession_cb(self, pboxid):
        del self.active_sessions[pboxid]

    def refreshSession(self, pboxid):
        if pboxid in self.active_sessions.keys():
            self.active_sessions[pboxid].cancel()
            timeout = reactor.callLater(NONCE_TIMEOUT * 60, self.killSession_cb, pboxid)
            self.active_sessions[pboxid] = timeout
        else:
            print "(SessionManager:RefreshSesson) Session not found for pboxid: " + pboxid

    def finishSession(self, pboxid):
        if pboxid in self.active_sessions.keys():
            del self.active_sessions[pboxid]
        else:
            print "(SessionManager:FinishSession) Session not found for pboxid: " + pboxid

# class AuthManager:
# This class provides a facility for generating and validating authentication challange nonces
# which will be signed by the client and sent back to the server inside an
# authentication request(startsession and second stage of register).
# A nonce is only valid for a single request and lasts for <NONCE_TIMEOUT> minutes.
class AuthManager(object):

    def __init__(self, identity):
        self.server = identity
        self.active_nonces = {}

    #generateNonce: returns base64 encoded nonce
    def generateNonce(self, cli_key):
        def removeNonce_cb(nonceid):
            del self.active_nonces[nonceid]

        if len(self.active_nonces.keys()) != 0 :
            nonceid = max(self.active_nonces.keys()) + 1
        else:
            nonceid = 0;

        nonce = str(Random.get_random_bytes(64))
        print nonce
        enc_nonce = self.server.encryptData(nonce , cli_key)
        timeout = reactor.callLater(NONCE_TIMEOUT * 60, removeNonce_cb, nonceid)
        self.active_nonces.update({nonceid: {'nonce': nonce,  'timeout': timeout}})
        return (enc_nonce, nonceid)

    #validateNonce: nonce must be base64 encoded //TODO: use PAM here.
    def validateNonce(self, signature, nonceid, cli_key):
        original = ""
        if nonceid in self.active_nonces.keys():
            self.active_nonces[nonceid]['timeout'].cancel()
            original = self.active_nonces[nonceid]['nonce']
            del self.active_nonces[nonceid]
        else:
            return False


        cli_key = RSA.importKey(cli_key)
        print original
        print signature
        signature = self.server.decryptData(signature)#TEST THIS!
        return self.server.verifySignature(signature, original, cli_key)
