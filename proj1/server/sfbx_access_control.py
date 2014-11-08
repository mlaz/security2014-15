from  sfbx_storage import SafeBoxStorage


#
# SafeBox server access control utilities API:
# Provides facilities and utilities for preforming access control related operations
#

# Some utilities:
#

# class ServerIdentity:
# This class provides a facility for managing the application's cryptographic identity
# and preforming cryptographic operations on given data.
class ServerIdentity():

    def __init__(self, keys_file_path, password):
        # f = open('private-key.pem', 'r')
        # self = priv_key = RSA.importKey(f.read(),  passphrase='some-pass')
        # f.close()
        return

    def encryptData(self, data):
        return 0

    def decryptData(self, data):
        return 0

    def signData(self, data):
        return 0

    def checkSignature(self, data, ext_pubkey):
        return 0

class TicketManager():

    def __init__(self, identity):
        self.server = identity
        self.active_tickets = {}

    def generateTicket():
        return 0

    def validateTicket():
        return 0

# class AccessCtrlHandler:
# This class provides a facility for validation of access permissions and client identity,
# which is done when handling every http request received.
class AccessCtrlHandler:

    def __init__(self, keys_file_path=0, password=0):
       self.server = ServerIdentity(keys_file_path, password)
       #self.ticket_manager = TicketManager(server)
       self.storage = SafeBoxStorage()

# PBoxes resource related operations:
#
    def handleListPBoxes(self, request):
        return self.storage.listPBoxes(request)

    def handleGetPBoxMData(self, request):
        return self.storage.getPBoxMData(request)

    def handleRegisterPBox(self, request):
        return self.storage.registerPBox(request)

# Files resource related operations:
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

# Share resource related operations:
#
