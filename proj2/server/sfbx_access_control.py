from twisted.internet import defer, reactor
from twisted.web.server import NOT_DONE_YET

from Crypto.PublicKey import RSA

from pprint import pprint
from base64 import *
import json

from sfbx_server_cryptography import ServerIdentity
from sfbx_authentication import TicketManager, SessionManager
from sfbx_storage import SafeBoxStorage, strip_text
from sfbx_cc_utils import get_subjdata_from_cert_str, validate_cert
NONCE_SIZE = 172 # size of signed nonce
USR_PASSWD_SIZE = 172
USR_CERT_SIZE = 3380
USR_SUBCA_SIZE = 3328
RSA_KEY_SIZE = 271

#
# SafeBox server access control utilities API:
# Provides facilities and utilities for preforming access control operations
#

# class AccessCtrlHandler:
# This class provides a facility for validation of access permissions and client identity,
# which is done when handling every http request received.
class AccessCtrlHandler(object):

    def __init__(self, keys_dirname=0, password=0):
       self.server = ServerIdentity(keys_dirname, password)
       self.ticket_manager = TicketManager(self.server)
       self.session_manager = SessionManager(self.server, self.ticket_manager)
       self.storage = SafeBoxStorage(self.server)

    # Handling Session resource related operations:
    #

    def handleGetKey(self):
        key = self.server.pub_key.exportKey('PEM')
        print key
        reply_dict = { 'status': "OK", 'key': key }
        return json.dumps(reply_dict, sort_keys=True, encoding="utf-8")

    # handleGetNonce:
    def handleGetNonce(self, request):
        key_txt = request.content.read()
        if not key_txt:
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "No key on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")

        print key_txt
        cli_key = RSA.importKey(key_txt)
        if not cli_key.can_encrypt():
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "Invalid key on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")


        (nonce, nonceid) = self.session_manager.getNonce(key_txt)
        reply_dict = { 'status': "OK", 'nonce': nonce, 'nonceid': nonceid}

        return json.dumps(reply_dict, sort_keys=True, encoding="utf-8")

    # handleStartSession: handles start session requests.
    def handleStartSession(self, request, nonce=None, passwd=None, ccid=None):
        nonceid = strip_text(str(request.args['nonceid']))
        nonceid = int(nonceid)
        if nonceid > -1:
            if not nonce:
                nonce = request.content.read(NONCE_SIZE)

            if not nonce:
                reply_dict = { 'status': {'error': "Invalid Request",
                                          'message': "No challange nonce on request body."} }
                return json.dumps(reply_dict, encoding="utf-8")
        else:
            nonce = None

        if passwd == None:
            passwd = request.content.read(USR_PASSWD_SIZE)


        def handleStartSession_cb(data):
            if not data:
                reply_dict = { 'status': {'error': "Invalid Request",
                                          'message': 'User does not exist.'} }

            else:
                pboxid = data[0][0]
                pubkey = data[0][1]
                salt = self.server.decryptData(data[0][2]) #TODO: STORE THIS ENCRYPTED
                #print pubkey
                print "StartSession salt:" , salt
                #print "encripted nonce: ", nonce
                if self.session_manager.startSession(nonce, nonceid, pubkey, pboxid, salt, passwd):
                    print "Valid Nonce!"
                    reply_dict = { 'status': "OK" }
                    ticket = self.ticket_manager.generateTicket(pboxid, pubkey)
                    request.addCookie('ticket', ticket)
                else:
                    print "Invalid Nonce!"
                    if request.args['method'] == ['retister']:
                        self.storage.deletePBox(pboxid)
                        reply_dict = { 'status': {'error': "Invalid Ticket",
                                        'message': 'Could not start session registeration dropped.'} }
                    else:
                        reply_dict = { 'status': {'error': "Invalid Nonce",
                                          'message': 'N/A'} }

            request.write( json.dumps(reply_dict, sort_keys=True, encoding="utf-8") )
            request.finish()

        d = self.storage.getClientData(request, ccid)
        d.addCallback(handleStartSession_cb)
        return NOT_DONE_YET

    # handleValidation: handles the validation process for a given method
    # only calls method if the provided ticket is valid.
    def handleValidation(self, request, method):
        #print "TICKET_FROM_COOKIE:", request.getCookie('ticket')
        ticket = request.getCookie('ticket')
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
                    d = method(request, pboxid, pubkey)
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
        def handleGetSession(data, request, nonce, passwd):
            if len(data) != 0:
                reply_dict = { 'status': {'error': "Unsuccessful db transaction", 'message': "N/A"} }
                request.write(json.dumps(reply_dict, encoding="utf-8"));
                request.finish()
            else:
                return self.handleStartSession(request, nonce, passwd, ccid)

        # Checking if the client exists.
        def checkClientExists_cb(data, nonce, key_txt, passwd_hash, salt, passwd):
            if data:
                reply_dict = { 'status': {'error': "Invalid Request",
                                          'message': 'User already exists.'} }
                request.write( json.dumps(reply_dict, sort_keys=True, encoding="utf-8") )
                request.finish()
            else:
                #TODO: validate certificates and keys here
                d = self.storage.registerPBox(name, ccid, key_txt, passwd_hash, salt)
                d.addCallback(handleGetSession, request, nonce, passwd)
                return NOT_DONE_YET

        #TODO: integrate this with content integrity validation
        nonce = request.content.read(NONCE_SIZE)
        if not nonce:
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "No challange nonce on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")

        # Hashing password:
        cry_passwd = request.content.read(USR_PASSWD_SIZE)
        print "Password:", cry_passwd
        #print type(passwd), "LEN:",len(passwd)
        cli_passwd = self.server.decryptData(cry_passwd)
        if not cli_passwd:
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "Invalid format for password on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")
        (passwd_hash, salt) = self.server.genHash(cli_passwd)

        #print "Register Salt:", salt

        # Extracting cc certificate
        cli_cert = b64decode(request.content.read(USR_CERT_SIZE))
        if not cli_cert:
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "No CC certificate on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")
        print "Client Certificate:", cli_cert

        # Extracting cc subca
        cli_subca = b64decode(request.content.read(USR_SUBCA_SIZE))
        if not cli_subca:
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "No CC subca on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")
        print "Client SubCA:", cli_subca

        # Validating certificate:
        (name, ccid) = get_subjdata_from_cert_str(cli_cert)
        print "NAME: ", name
        print "CCID: ", ccid
        if validate_cert(cli_cert, cli_subca) == False:
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "Invalid CC subca on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")
        print "Certificate Valid"

        # Validating key:
        key_txt = request.content.read(RSA_KEY_SIZE)
        if not key_txt:
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "No key on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")

        cli_key = RSA.importKey(key_txt)
        if not cli_key.can_encrypt():
            reply_dict = { 'status': {'error': "Invalid Request",
                                      'message': "Invalid key on request body."} }
            return json.dumps(reply_dict, encoding="utf-8")

        d = self.storage.getClientData(request, ccid)
        d.addCallback(checkClientExists_cb, nonce, key_txt, passwd_hash, salt, cry_passwd)

        return NOT_DONE_YET

    # Handling Files resource related operations:
    #
    def handleListFiles(self, request):
        return self.handleValidation(request, self.storage.listFiles)

    def handleGetFileMData(self, request):
        return self.handleValidation(request, self.storage.getFileMData)

    def handleGetFile(self, request):
        return self.handleValidation(request, self.storage.getFile)

    def handlePutFile(self, request):
        return self.handleValidation(request, self.storage.putFile)

    def handleUpdateFile(self, request):
       return self.handleValidation(request, self.storage.updateFile)

    def handleDeleteFile(self, request):
        return self.handleValidation(request, self.storage.deleteFile)

    # Handling Share resource related operations:
    #

    def handleShareFile(self, request):
        return self.handleValidation(request, self.storage.shareFile)

    def handleGetShareMData(self, request):
        return self.handleValidation(request, self.storage.getShareMData)

    def handleGetShared(self, request):
        return self.handleValidation(request, self.storage.getShared)

    def handleListShares(self, request):
        return self.handleValidation(request, self.storage.listShares)

    def handleUpdateShared(self, request):
        return self.handleValidation(request, self.storage.updateShared)

    def handleUpdateSharePerm(self, request):
        return self.handleValidation(request, self.storage.updateSharePerm)

    def handleDeleteShare(self, request):
        return self.handleValidation(request, self.storage.deleteShare)
