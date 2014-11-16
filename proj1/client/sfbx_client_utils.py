from twisted.internet import reactor
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers
from twisted.internet import abstract
from twisted.web.server import NOT_DONE_YET
from twisted.web import iweb, http_headers
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.protocols.ftp import FileConsumer
from sfbx_client_protocols import FileDownload

from base64 import b64encode, b64decode
from StringIO import StringIO
from pprint import pformat
from pprint import pprint
from zope import interface
import os
import json

from sfbx_client_cryptography import *
from sfbx_client_protocols import *
from sfbx_fs_utils import _FileProducer

# SafeBoxClient():
class SafeBoxClient():
    def __init__(self, server_addr="localhost:8000"):
        self.server_addr = server_addr
        self.client_id = self.ccid = self.ccid = None

    #initializes the client's remaining attributes
    def startClient(self, ccid, passwd, name):

        # checking if client is already registered
        def checkClientReg_cb(ticket):
            if ticket is None:
                print "User not registered..."
                if name is "":
                    print "Please provide your name for registry."
                    reactor.stop()
                else:
                    print "Registering user."
                    return self.handleRegister(name)

        # Instanciating ClientIdentity
        def startClientId_cb(key):
            self.client_id = ClientIdentity(self.ccid, passwd, key)
            self.handleGetTicket(checkClientReg_cb)

        self.ccid = ccid
        return self.handleGetKey(startClientId_cb)


    # handleGetKey: handles getkey operations
    def handleGetKey(self, method):
        def handleGetKey_cb(response):
            defer = Deferred()
            defer.addCallback(method)
            response.deliverBody(DataPrinter(defer, "getkey"))
            return NOT_DONE_YET

        agent = Agent(reactor)
        headers = http_headers.Headers()
        d = agent.request(
                    'GET',
                    'http://localhost:8000/session/?method=getkey',
            headers,
            None)

        d.addCallback(handleGetKey_cb)

        return NOT_DONE_YET

    # handleGetTicket: handles getticket operations
    def handleGetTicket(self, method, data=None):
        def handleGetTicket_cb(response):
            defer = Deferred()
            if data:
                defer.addCallback(method, data)
            else:
                defer.addCallback(method)

            response.deliverBody(getTicket(defer, self.client_id))
            return NOT_DONE_YET

        agent = Agent(reactor)
        headers = http_headers.Headers()
        d = agent.request(
                'GET',
                'http://localhost:8000/session/?method=getticket&ccid='
            + self.ccid,
            headers,
            None)

        d.addCallback(handleGetTicket_cb)

        return NOT_DONE_YET

    # handleRegister: Handles register commands.
    def handleRegister(self, name):

        agent = Agent(reactor)
        body = FileBodyProducer(StringIO(self.client_id.pub_key.exportKey('PEM')))
        headers = http_headers.Headers()
        d = agent.request(
            'PUT',
            'http://localhost:8000/pboxes/?method=register&ccid='
            + self.ccid
            + '&name=' + name,
            headers,
            body)

        return NOT_DONE_YET

    # handleList: handles every list command
    def handleList(self, line):
        def handleList_cb(response):
            defer = Deferred()
            response.deliverBody(DataPrinter(defer, "list"))
            return NOT_DONE_YET

        def handleListPboxes(signedTicket):
            print len(signedTicket)
            agent = Agent(reactor)
	    body = FileBodyProducer(StringIO(signedTicket))
            headers = http_headers.Headers()
            d = agent.request(
                    'GET',
                    'http://localhost:8000/pboxes/?method=list&ccid='
                + self.ccid,
                headers,
                body)
            d.addCallback(handleList_cb)
            return NOT_DONE_YET

        def handleListFiles(signedTicket):
            agent = Agent(reactor)
            body = FileBodyProducer(StringIO(signedTicket))
            headers = http_headers.Headers()
	    d = agent.request(
                    'GET',
                    'http://localhost:8000/files/?method=list&ccid='
                + self.ccid,
                headers,
                body)
            d.addCallback(handleList_cb)
            return NOT_DONE_YET

        s = line.split()
        if len(s) == 2:
            if s[1].lower() == "pboxes":
                return self.handleGetTicket(handleListPboxes)
            elif s[1].lower() == "files":
		return self.handleGetTicket(handleListFiles)
	    else:
		print "Error: invalid arguments!\n"
		print "Correct usage: list <pboxes|files>"
        else:
	    print "Error: invalid arguments!\n"
            print "Correct usage: list <pboxes|files>"


    # handleGetMData: Handles get pbox metadata operations.
    def handleGetMData(self, ticket, data):
        #data = (method, tgtccid)
        pprint(data)
        def handleGetMData_cb(response):
            defer = Deferred()
            defer.addCallback(data[0])
            response.deliverBody(DataPrinter(defer, "getmdata"))
            return NOT_DONE_YET

        agent = Agent(reactor)
        body = FileBodyProducer(StringIO(ticket))
        headers = http_headers.Headers()
        d = agent.request(
			'GET',
            'http://localhost:8000/pboxes/?method=get_mdata&ccid='
            + self.ccid + "&tgtccid=" + data[1],
            headers,
            body)

        d.addCallback(handleGetMData_cb)

        return NOT_DONE_YET

        # handleGetFileMData: Handles get pbox metadata operations.
    def handleGetFileMData(self, ticket, data):
        #data = (method, fileid)
        def handleGetFileMData_cb(response):
            defer = Deferred()
            defer.addCallback(data[0])
            response.deliverBody(DataPrinter(defer, "getmdata"))
            return NOT_DONE_YET

        agent = Agent(reactor)
        body = FileBodyProducer(StringIO(ticket))
        headers = http_headers.Headers()
        d = agent.request(
			'GET',
            'http://localhost:8000/files/?method=get_mdata&ccid='
            + self.ccid + "&fileid=" + data[1],
            headers,
            body)

        d.addCallback(handleGetFileMData_cb)

        return NOT_DONE_YET

    # handleGet: handles get file
    def handleGet(self, line):
        def printResult_cb(data):
            pprint(data) #TODO: Format this!
            return NOT_DONE_YET

        # for info requests
        def handleGetInfo_cb(ticket):
            s = line.split()
            if s[1].lower() == "pboxinfo":
                return self.handleGetMData(ticket,
                                               (printResult_cb, s[2].lower()))
            elif s[1].lower() == "fileinfo":
                return self.handleGetFileMData(ticket,
                                               (printResult_cb, s[2].lower()))

        # Decrypt and write the file
        def writeFile(ignore): #we should implement http error code checking
            s = line.split()
            enc_file = open(fileId, "r")
            if len(s) == 4:
                dec_file = open(s[3], "w")
            else:
                dec_file = open(fileId + "_decrypted", "w")

            enc_key = enc_file.read(IV_KEY_SIZE_B64)
            # print "debugging: iv key writefile"
            # print enc_key
            print "Decrypting file..."
            key = self.client_id.decryptData(enc_key)
            enc_iv = enc_file.read(IV_KEY_SIZE_B64)
            #print enc_iv
            iv = self.client_id.decryptData(enc_iv)
            print iv
            self.client_id.decryptFileSym(enc_file, dec_file, key, iv)
            print "File written."

        # for get file
        def handleGetFile(signedTicket):
            def handleGetFile_cb(response, f):
                finished = Deferred()
                finished.addCallback(writeFile)
                cons = FileConsumer(f)
                response.deliverBody(FileDownload(finished, cons))
                print "Downloading file..."
                return finished

            agent = Agent(reactor)
            body = FileBodyProducer(StringIO(signedTicket))
            headers = http_headers.Headers()
            d = agent.request(
                    'GET',
                    'http://localhost:8000/files/?method=getfile&ccid=' + self.ccid
                + '&fileid=' + fileId,
                    headers,
                    body)
            f = open(fileId, "w")
            d.addCallback(handleGetFile_cb, f)
            return NOT_DONE_YET

        s = line.split()
        if len(s) == 3:
            #if s[1].lower() == "file":
             #   fileId = s[2]
              #  return self.handleGetTicket(handleGetFile)
            if s[1].lower() == "pboxinfo":
                return self.handleGetTicket(handleGetInfo_cb)
            elif s[1].lower() == "fileinfo":
                return self.handleGetTicket(handleGetInfo_cb)
            else:
                print "Error: invalid arguments!\n"
                print "Correct usage: get file <fileId> or get pboxinfo <PBox Owners CC Number>"
        elif len(s) == 4:
            if s[1].lower() == "file":
                fileId = s[2]
                return self.handleGetTicket(handleGetFile)

            else:
                print "Error: invalid arguments!\n"
                print "Correct usage: get file <fileId> <dest. filename on filesystem.>"
        else:
	    print "Error: invalid arguments!\n"

    # printPutReply_cb: prints put and update responses
    def printPutReply_cb(self,response):
            print "Done."

            defer = Deferred()
            response.deliverBody(DataPrinter(defer, "getmdata"))
            return NOT_DONE_YET


    # handlePutFile: handles file upload
    def handlePutFile(self, line):

        def putFile_cb(ticket):
            print "Encrypting file..."
            s = line.split()
            file = open(s[2], 'r')
            enc_file = open("enc_fileout", 'w')
            crd = self.client_id.encryptFileSym(file, enc_file)
            agent = Agent(reactor)
            dataq = []
            dataq.append(ticket)
            dataq.append( self.client_id.encryptData(crd[0], self.client_id.pub_key))
            dataq.append( self.client_id.encryptData(crd[1]) )
            #print crd[1]
            # print "debugging:key, iv putfile"
            # print dataq[1]
            # print len(dataq[1])
            # print dataq[2]
            # print len(dataq[2])
            print "Uploading file..."
            enc_file = open("enc_fileout", 'r')
            body = _FileProducer(enc_file ,dataq)
            headers = http_headers.Headers()
            d = agent.request(
                'PUT',
                'http://localhost:8000/files/?method=putfile&ccid='
                + self.ccid + "&name=" + os.path.basename(s[2]),
                headers,
                body)
            d.addCallback(self.printPutReply_cb)

            return NOT_DONE_YET

        s = line.split()
        if len(s) != 3:
            print "Error: invalid arguments!\n"
            return
        else:
            if s[1].lower() != "file":
                print "Error: invalid arguments!\n"
                print "Usage: put file <filepath>"
                return
            elif not os.path.exists(s[2]):
                print "Error: File " + s[2] + " does not exist.\n"
                return

        return self.handleGetTicket(putFile_cb)

    #handles update commands
    def handleUpdate(self, line):
        def updateFile_cb(ticket, iv):
            #data = (key,)
            print "Updating file..."
            s = line.split()
            agent = Agent(reactor)
            dataq = []
            dataq.append(ticket)
            dataq.append( iv )
            # print "debugging:ticket, iv updatefile"
            # print dataq[0]
            # print dataq[1]
            # print len(dataq[1])
            print "Uploading file..."
            enc_file = open("enc_fileout", 'r')
            body = _FileProducer(enc_file ,dataq)
            headers = http_headers.Headers()
            d = agent.request(
                'POST',
                'http://localhost:8000/files/?method=updatefile&ccid='
                + self.ccid + "&name=" + os.path.basename(s[3]) + "&fileid=" + s[2] ,
                headers,
                body)
            d.addCallback(self.printPutReply_cb)

            return NOT_DONE_YET

        def encryptFile_cb(data):
            s = line.split()
            #pprint(data)
	    if isinstance(data, basestring):
		print data
                return

            print "Encrypting file..."
            #print data["data"]["SymKey"]
            enc_key = data["data"]["SymKey"]
            key = self.client_id.decryptData(enc_key, self.client_id.priv_key)
            #print len(key)
            file = open(s[3], 'r')
            enc_file = open("enc_fileout", 'w')
            crd = self.client_id.encryptFileSym(file, enc_file, key=key)

            new_iv =  self.client_id.encryptData(crd[1])
            return self.handleGetTicket(updateFile_cb, new_iv)


        s = line.split()
        if len(s) == 4:
            if not os.path.exists(s[3]):
                print "Error: File " + s[3] + " does not exist.\n"
                return
            hfmd_data = (encryptFile_cb, s[2])
            return self.handleGetTicket(self.handleGetFileMData, hfmd_data)

        else:
            if s[1].lower() !="file":
                print "Error: invalid arguments!\n"
                print "Usage: update <file|share> <fileid|shareid> <local file path>"
                return
            elif not os.path.exists(s[2]):
                print "Error: File " + s[2] + " does not exist.\n"
                return


    # handleDelete: handles delete commands
    def handleDelete(self, line):
        def printDeleteReply_cb(data):
            if not data:
                print "Done."
            else:
                pprint(data)

        def deleteFile_cb(ticket):
            agent = Agent(reactor)
            body = FileBodyProducer(StringIO(ticket))
            headers = http_headers.Headers()
            d = agent.request(
                'DELETE',
                'http://localhost:8000/files/?method=delete&ccid='
                + self.ccid + "&fileid=" + s[2],
                headers,
                body)

            d.addCallback(printDeleteReply_cb)


        s = line.split()
        if len(s) == 3:
            return self.handleGetTicket(deleteFile_cb)

        else:
            if s[1].lower() !="file":
                print "Error: invalid arguments!\n"
                print "Usage: delete <file|share> <fileid|shareid>"
                return
            elif not os.path.exists(s[2]):
                print "Error: File " + s[2] + " does not exist.\n"
                return

        return

    def handleShare(self, line):

        def getFKey_cb(data):
            enc_key = data["data"]["SymKey"]

            def getDstKey_cb(data):
                dstkey = data["data"]["PubKey"]
                print "pubkey" + dstkey

                def shareFile_cb(ticket):
                    agent = Agent(reactor)
                    dataq = []
                    dataq.append(ticket)
                    dataq.append(enc_sym_key)
                    print "Uploading symkey..."
                    body = _FileProducer(StringIO("") ,dataq)
                    headers = http_headers.Headers()
                    d = agent.request(
                        'PUT',
                        'http://localhost:8000/shares/?method=sharefile&ccid='
                        + self.ccid + "&rccid=" + s[3] + "&fileid=" + s[2],
                        headers,
                        body)
                    d.addCallback(self.printPutReply_cb)

                    return d

                #enc_key = data["data"]["SymKey"]
                sym_key = self.client_id.decryptData(enc_key, self.client_id.priv_key)
                dstkey = RSA.importKey(dstkey)
                enc_sym_key = self.client_id.encryptData(sym_key, dstkey)
                return self.handleGetTicket(shareFile_cb, None)



            hfmd_data = (getDstKey_cb, s[3].lower())
            return self.handleGetTicket(self.handleGetMData, hfmd_data)

        s = line.split()
        if len(s) == 4:
            hmd_data = (getFKey_cb, s[2].lower())
            return self.handleGetTicket(self.handleGetFileMData, hmd_data)

        else:
            if s[1].lower() != "file":
                print "Error: invalid arguments!\n"
                print "Usage: share file <fileid> <recipient's ccid>"
                return
