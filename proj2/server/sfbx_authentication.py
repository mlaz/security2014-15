from twisted.internet import defer, reactor
from Crypto.Hash import SHA256
from Crypto import Random
from Crypto.Util import number
from Crypto.PublicKey import RSA

from sfbx_server_cryptography import ServerIdentity

from pprint import pprint
from base64 import *
import PAM

NONCE_TIMEOUT = 3
TICKET_TIMEOUT = 3
TICKET_SIZE = 172 # size of signed ticket

class TicketManager(object):

    def __init__(self, identity):
        self.server = identity
        self.active_tickets = {}

    # removeTicket_cb: removes a ticket
    def removeTicket(self, pboxid):
        if pboxid in self.active_tickets.keys():
            del self.active_tickets[pboxid]

    # generateTicket: returns base64 encoded ticket
    def generateTicket(self, pboxid, cli_key):

        if pboxid in self.active_tickets.keys():
            del self.active_tickets[pboxid]

        ticket = Random.get_random_bytes(64)
        #pprint(ticket)
        #print type(ticket)
        #cli_key = RSA.importKey(cli_key)
        enc_ticket = self.server.encryptData(str(ticket) , cli_key)
        self.active_tickets.update({pboxid: {'ticket': ticket}})
        return enc_ticket

    def getTicketRaw(self, pboxid):
        if pboxid in self.active_tickets.keys():
            return self.active_tickets[pboxid]['ticket']
        else:
            return None

    def getTicket(self, pboxid, cli_key):
        if pboxid in self.active_tickets.keys():
            return self.server.encryptData(str(self.active_tickets[pboxid]['ticket']) , cli_key)
        else: return self.generateTicket(pboxid, cli_key)

    # validateTicket: ticket must be base64 encoded
    def validateTicket(self,signature, pboxid, cli_key):
        original = ""
        if pboxid in self.active_tickets.keys():
            #print "Original:", number.bytes_to_long(self.active_tickets[pboxid]['ticket'])
            original = number.long_to_bytes(number.bytes_to_long(self.active_tickets[pboxid]['ticket']) + long("1", base=10))
            #print "Incrementado:", number.bytes_to_long(original)
            self.active_tickets[pboxid] = {'ticket': original}
        else:
            return False

        cli_key = RSA.importKey(cli_key)
        #print signature
        signature = self.server.decryptData(signature)#TEST THIS!
        return self.server.verifySignature(signature, original, cli_key)

# class SessionManager:
# This class provides a facility for starting maintaining sessions
# A Session is only valid for a single request and lasts for <SESSION_TIMEOUT> minutes.
class SessionManager(object):

    def __init__(self, identity, ticket_manager):
        self.server = identity
        self.authm = AuthManager(identity)
        self.ticket_manager = ticket_manager
        self.active_sessions = {}

    def getNonce(self, cli_key):
        return self.authm.generateNonce(cli_key)

    def startSession(self, signature, nonceid, cli_key, pboxid, salt, passwd):
        if pboxid in self.active_sessions.keys():
            self.killSession(pboxid)

        ret = False
        if int(nonceid) < 0:

            pwd = self.server.decryptData(passwd)
            (pwd_hash, s) = self.server.genHash(pwd, salt)

            # PAM conversation
            def pam_conv(auth, query_list, userData):
                resp = []

                for i in range(len(query_list)):
                    query, type = query_list[i]
                    if query == 'Original:':
                        resp.append(('', 0))
                    elif query == 'Signature:':
                        resp.append(('', 0))
                    else:
                        resp.append((pwd_hash, 0))
                return resp

            auth = PAM.pam()
            auth.start('myservice')
            auth.set_item(PAM.PAM_USER, str(pboxid))
            auth.set_item(PAM.PAM_CONV, pam_conv)
            try:
                auth.authenticate()
            except PAM.error, resp:
                print 'AUTH FAIL (%s)' % resp
            except:
                print 'PAM module error'
            else:
                ret = True

                if ret == True:
                    timeout = reactor.callLater(NONCE_TIMEOUT * 60, self.killSession, pboxid)
                    self.active_sessions.update({pboxid : timeout})
                    print "Password Accepted"

            return ret

        if self.authm.validateNonce (signature, nonceid, pboxid):
            timeout = reactor.callLater(NONCE_TIMEOUT * 60, self.killSession, pboxid)
            self.active_sessions.update({pboxid : timeout})
            print "Valid Challange"
            return True
        else:
            return False

    def hasSession(self, pboxid):
        return pboxid in self.active_sessions.keys()

    def killSession(self, pboxid):
        if pboxid in self.active_sessions.keys():
            if not self.active_sessions[pboxid].called:
                self.active_sessions[pboxid].cancel()
            self.ticket_manager.removeTicket(pboxid)
            del self.active_sessions[pboxid]
            print "(SessionManager:KillSesson) Session killed for pboxid: ", pboxid
        else:
            print "(SessionManager:KillSession) Session not found for pboxid: ", pboxid

    def refreshSession(self, pboxid):
        if pboxid in self.active_sessions.keys():
            if not self.active_sessions[pboxid].called:
                self.active_sessions[pboxid].cancel()
            timeout = reactor.callLater(NONCE_TIMEOUT * 60, self.killSession, pboxid)
            self.active_sessions[pboxid] = timeout
        else:
            print "(SessionManager:RefreshSesson) Session not found for pboxid: ", pboxid

# class AuthManager:
# This class provides a facility for generating and validating authentication challange nonces
# which will be signed by the client and sent back to the server inside an
# authentication request(startsession and second stage of register).
# A nonce is only valid for a single request and lasts for <NONCE_TIMEOUT> minutes.
class AuthManager(object):

    def __init__(self, identity):
        self.server = identity
        self.active_nonces = {}

    # generateNonce: returns base64 encoded nonce
    def generateNonce(self, cli_key):
        def removeNonce_cb(nonceid):
            del self.active_nonces[nonceid]

        if len(self.active_nonces.keys()) != 0 :
            nonceid = max(self.active_nonces.keys()) + 1
        else:
            nonceid = 0;

        nonce = str(Random.get_random_bytes(64))
        #print nonce
        enc_nonce = self.server.encryptData(nonce , cli_key)
        timeout = reactor.callLater(NONCE_TIMEOUT * 60, removeNonce_cb, nonceid)
        self.active_nonces.update({nonceid: {'nonce': nonce,  'timeout': timeout}})
        return (enc_nonce, nonceid)

    # validateNonce: validates the signed nonce using PAM
    def validateNonce(self, signature, nonceid, pboxid):
        ret = False

        original = ""
        if nonceid in self.active_nonces.keys():
            self.active_nonces[nonceid]['timeout'].cancel()
            original = self.active_nonces[nonceid]['nonce']
            del self.active_nonces[nonceid]
        else:
            print "Couldn't find Nonce!"
            return False

        signature = self.server.decryptData(signature)
        #print 'Original before: ', original
        #print 'Signature before: ', signature

        # PAM conversation
        def pam_conv(auth, query_list, userData):
            resp = []

            for i in range(len(query_list)):
                query, type = query_list[i]
                #print query
                #print "ORIGINAL: ", b64encode(original)
                if query == 'Original:':
                        resp.append((b64encode(original), 0))
                elif query == 'Signature:':
                        resp.append((b64encode(signature), 0))
                else:
                        resp.append(('', 0))
            return resp

        auth = PAM.pam()
        auth.start('myservice')
        auth.set_item(PAM.PAM_USER, str(pboxid))
        auth.set_item(PAM.PAM_CONV, pam_conv)
        try:
            auth.authenticate()
        except PAM.error, resp:
            print 'AUTH FAIL (%s)' % resp
        except:
            print 'PAM module error'
        else:
            ret = True

        return ret
