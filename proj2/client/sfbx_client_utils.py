from twisted.internet import reactor
from twisted.web.client import Agent, CookieAgent, FileBodyProducer
from twisted.web.http_headers import Headers
from twisted.internet import abstract
from twisted.web.server import NOT_DONE_YET
from twisted.web import iweb, http_headers
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.protocols.ftp import FileConsumer
from sfbx_client_protocols import FileDownload

from cookielib import CookieJar
from base64 import b64encode, b64decode
from StringIO import StringIO
from pprint import pformat
from pprint import pprint
from zope import interface
from M2Crypto import X509
import os
import json
import Cookie

from sfbx_client_cryptography import *
from sfbx_client_protocols import *
from sfbx_fs_utils import _FileProducer
import sfbx_cc_utils as cc

# SafeBoxClient():
class SafeBoxClient():
    def __init__(self, server_addr="localhost:8000"):
        self.server_addr = server_addr
        self.client_id = self.ccid = self.pin = None
        self.cookie_jar = CookieJar()
        self.curr_ticket = ""

    # startClient: Initializes the client's remaining attributes,
    # this implies starting a session and eventually client registration.
    def startClient(self, ccid, passwd, name, pin):

        # checking if client is already registered
        def checkClientReg_cb(success):
            if success == False:
                print "User not registered."
                if pin is None:
                    print "Please provide your Citizen Card for registration"
                    reactor.stop()
                else:
                    print "Registering user..."
                    return self.handleRegister()
            #pprint(self.cookie_jar.__dict__)
            for cookie in self.cookie_jar:
                #print cookie
                #print type(cookie)
                self.curr_ticket = self.client_id.decryptData(cookie.value)

        # Instanciating ClientIdentity
        def startClientId_cb(key):
            self.client_id = ClientIdentity(self.ccid, passwd, key)
            self.handleStartSession(checkClientReg_cb)

        self.ccid = ccid
        if pin is not None:
			self.pin = pin
        return self.handleGetKey(startClientId_cb)

# Session, Registry and Authentication related opreations
#
    # handleGetKey: handles getkey operations, this happens as the
    # first step of the startClient operation.
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

    # handleStartSession: handles startsession operations
    def handleStartSession(self, method):
        def procResponse_cb(response):
            defer = Deferred()
            defer.addCallback(method)
            response.deliverBody(DataPrinter(defer, "bool"))
            return NOT_DONE_YET

        def startSession_cb((signedNonce, nonceid)):
            agent = CookieAgent(Agent(reactor), self.cookie_jar)
            dataq = []
            dataq.append(signedNonce)
            body = _FileProducer(StringIO(self.client_id.encryptData(self.client_id.password)) ,dataq)
            headers = http_headers.Headers()
	    d = agent.request(
                'PUT',
                'http://localhost:8000/session/?method=startsession&ccid='
                + self.ccid + '&nonceid=' + str(nonceid),
                headers,
                body)
            d.addCallback(procResponse_cb)
            return NOT_DONE_YET

        def getNonce_cb(response):
            defer = Deferred()
            defer.addCallback(startSession_cb)
            response.deliverBody(getNonce(defer, self.client_id))
            return NOT_DONE_YET

        agent = Agent(reactor)
        body = FileBodyProducer(StringIO(self.client_id.pub_key.exportKey('PEM')))
        headers = http_headers.Headers()
        d = agent.request(
            'GET',
            'http://localhost:8000/session/?method=getnonce',
            headers,
            body)

        d.addCallback(getNonce_cb)

        return NOT_DONE_YET

    # handleRegister: Handles the registration process. Also part of the startClient operation.
    def handleRegister(self):
        def checkClientReg_cb(success):
            if success == False:
                print "ERROR: Couldn't register user."
                reactor.stop()

            #pprint(self.cookie_jar.__dict__)
            for cookie in self.cookie_jar:
                #print cookie
                #print type(cookie)
                self.curr_ticket = self.client_id.decryptData(cookie.value)
            print "Registration Successful."
        def procResponse_cb(response, method):
            defer = Deferred()
            defer.addCallback(method)
            response.deliverBody(DataPrinter(defer, "bool"))
            return NOT_DONE_YET

        def register_cb((signedNonce, nonceid)):
            agent = CookieAgent(Agent(reactor), self.cookie_jar)
            dataq = []
            dataq.append(signedNonce)
            dataq.append(self.client_id.encryptData(self.client_id.password))
            # Sending the Certificate and the Sub CA to the server
            if self.pin is  None:
                print "ERROR! Check the pin!"
                reactor.stop()
            cert = cc.get_certificate(cc.CERT_LABEL, self.pin)
            #print type(cert.as_pem())
            #print cert.as_pem()
            if cert is None:
                print "ERROR! Check the pin"
                reactor.stop()
            subca = cc.get_certificate(cc.SUBCA_LABEL, self.pin)
            #print type(subca.as_pem())
            #print subca.as_pem()
            if subca is None:
                print "ERROR! Check the pin"
                reactor.stop()
            print "cert len: ", len(self.client_id.encryptData(cert.as_pem()))
            print "sub ca len: ", len(self.client_id.encryptData(subca.as_pem()))
            dataq.append(self.client_id.encryptData(cert.as_pem()))
            dataq.append(self.client_id.encryptData(subca.as_pem()))
                
            body = _FileProducer(StringIO(self.client_id.pub_key.exportKey('PEM')) ,dataq)
            headers = http_headers.Headers()
            #print "Password:", self.client_id.encryptData(self.client_id.password)
            #print "LEN:", len(self.client_id.encryptData(self.client_id.password))
            d = agent.request(
                'PUT',
                'http://localhost:8000/pboxes/?method=register'
                + '&nonceid=' + str(nonceid),
                headers,
                body)
            d.addCallback(procResponse_cb, checkClientReg_cb)

        def getNonce_cb(response):
            defer = Deferred()
            defer.addCallback(register_cb)
            response.deliverBody(getNonce(defer, self.client_id))
            return NOT_DONE_YET

        agent = Agent(reactor)
        body = FileBodyProducer(StringIO(self.client_id.pub_key.exportKey('PEM')))
        headers = http_headers.Headers()
        d = agent.request(
            'GET',
            'http://localhost:8000/session/?method=getnonce',
            headers,
            body)

        d.addCallback(getNonce_cb)
        return NOT_DONE_YET

    def processCookie(self, uri):
        dci = number.long_to_bytes(number.bytes_to_long(self.curr_ticket) + long("1", base=10))
        #print "incremented ticket", number.bytes_to_long(dci)
        self.curr_ticket = dci
        sci = self.client_id.signData(str(dci))
        enc = self.client_id.encryptData(sci)
        for cookie in self.cookie_jar:
            cookie.value = enc
            cookie.path = uri
            self.cookie_jar.clear()
            self.cookie_jar.set_cookie(cookie)
        #print cookie

# List Operations
#
    # handleList: handles every list command
    def handleList_cb(self, response):
        defer = Deferred()
        response.deliverBody(DataPrinter(defer, "list"))
        return NOT_DONE_YET

    def handleListPboxes(self):
        self.processCookie("/pboxes")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        headers = http_headers.Headers()
        d = agent.request(
            'GET',
            'http://localhost:8000/pboxes/?method=list&ccid='
            + self.ccid,
            headers,
            None)
        d.addCallback(self.handleList_cb)
        return NOT_DONE_YET

    def handleListFiles(self):
        self.processCookie("/files")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        headers = http_headers.Headers()
        d = agent.request(
            'GET',
            'http://localhost:8000/files/?method=list&ccid='
            + self.ccid,
            headers,
            None)
        d.addCallback(self.handleList_cb)
        return NOT_DONE_YET

    def handleListShares(self):
        self.processCookie("/shares")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        headers = http_headers.Headers()
        d = agent.request(
            'GET',
            'http://localhost:8000/shares/?method=list&ccid='
            + self.ccid,
            headers,
            None)
        d.addCallback(self.handleList_cb)
        return NOT_DONE_YET

# Get Operations
#
    # handleGetMData: Handles get pbox metadata operations.
    def handleGetMData(self, data):
        #data = (method, tgtccid)
        pprint(data)
        def handleGetMData_cb(response):
            defer = Deferred()
            defer.addCallback(data[0])
            response.deliverBody(DataPrinter(defer, "getmdata"))
            return NOT_DONE_YET


        self.processCookie("/pboxes")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        headers = http_headers.Headers()
        d = agent.request(
			'GET',
            'http://localhost:8000/pboxes/?method=get_mdata&ccid='
            + self.ccid + "&tgtccid=" + data[1],
            headers,
            None)

        d.addCallback(handleGetMData_cb)

        return NOT_DONE_YET

    # handleGetFileMData: Handles get file metadata operations.
    def handleGetFileMData(self, data):
        #data = (method, fileid)
        def handleGetFileMData_cb(response):
            defer = Deferred()
            defer.addCallback(data[0])
            response.deliverBody(DataPrinter(defer, "getmdata"))
            return NOT_DONE_YET

        self.processCookie("/files")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        headers = http_headers.Headers()
        d = agent.request(
            'GET',
            'http://localhost:8000/files/?method=get_mdata&ccid='
            + self.ccid + "&fileid=" + data[1],
            headers,
            None)

        d.addCallback(handleGetFileMData_cb)

        return NOT_DONE_YET

    # handleGetShareMData: Handles get share metadata operations.
    def handleGetShareMData(self, data):
        #data = (method, fileid)
        def handleGetShareMData_cb(response):
            defer = Deferred()
            defer.addCallback(data[0])
            response.deliverBody(DataPrinter(defer, "getmdata"))
            return NOT_DONE_YET

        self.processCookie("/shares")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        headers = http_headers.Headers()
        d = agent.request(
			'GET',
            'http://localhost:8000/shares/?method=get_mdata&ccid='
            + self.ccid + "&fileid=" + data[1],
            headers,
            None)

        d.addCallback(handleGetShareMData_cb)

        return NOT_DONE_YET

    # handleGet: handles get file
    #def handleGet(self, line):
    def printResult_cb(self, data):
        pprint(data) #TODO: Format this!
        return NOT_DONE_YET

    # for info requests
    def handleGetInfo(self, s):
        if s[1].lower() == "pboxinfo":
            return self.handleGetMData((self.printResult_cb, s[2].lower()))
        elif s[1].lower() == "fileinfo":
            return self.handleGetFileMData((self.printResult_cb, s[2].lower()))
        elif s[1].lower() == "shareinfo":
            return self.handleGetShareMData((self.printResult_cb, s[2].lower()))

    # Decrypt and write the file
    def writeFile_cb(self, ignore, s): #we should implement http error code checking
        fileId = s[2]
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
    def handleGetFile(self, s):
        def handleGetFile_cb(response, f):
            finished = Deferred()
            finished.addCallback(self.writeFile_cb, s)
            cons = FileConsumer(f)
            response.deliverBody(FileDownload(finished, cons))
            print "Downloading file..."
            return finished

        fileId = s[2]
        self.processCookie("/files")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        headers = http_headers.Headers()
        d = agent.request(
            'GET',
            'http://localhost:8000/files/?method=getfile&ccid=' + self.ccid
            + '&fileid=' + fileId,
            headers,
            None)
        f = open(fileId, "w")
        d.addCallback(handleGetFile_cb, f)
        return NOT_DONE_YET

    # for get shared
    def handleGetShared(self, s):
        def handleGetShared_cb(response, f):
            finished = Deferred()
            finished.addCallback(self.writeFile_cb, s)
            cons = FileConsumer(f)
            response.deliverBody(FileDownload(finished, cons))
            print "Downloading file..."
            return finished

        fileId = s[2]
        self.processCookie("/shares")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        headers = http_headers.Headers()
        d = agent.request(
            'GET',
            'http://localhost:8000/shares/?method=getshared&ccid=' + self.ccid
            + '&fileid=' + fileId,
            headers,
            None)
        f = open(fileId, "w")
        d.addCallback(handleGetShared_cb, f)
        return NOT_DONE_YET

# Put Operations
    # printPutReply_cb: prints put and update responses
    def printPutReply_cb(self, response):
        print "Done."

        defer = Deferred()
        response.deliverBody(DataPrinter(defer, "getmdata"))
        return NOT_DONE_YET

    # handlePutFile: handles file upload
    def handlePutFile(self, line):
        print "Encrypting file..."
        s = line.split()
        file = open(s[2], 'r')
        enc_file = open("enc_fileout", 'w')
        crd = self.client_id.encryptFileSym(file, enc_file)
        self.processCookie("/files")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        dataq = []
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

# Update Operations
#
    #handles update commands
    def handleUpdate(self, s):
        def encryptFile_cb(data):#TODO: Some error checking here.

            def updateFile_cb(iv):
                #data = (key,)
                print "Updating file..."
                self.processCookie("/files")
                agent = CookieAgent(Agent(reactor), self.cookie_jar)
                dataq = []
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

            def updateShared_cb(iv):
                print "Updating file..."
                self.processCookie("/shares")
                agent = CookieAgent(Agent(reactor), self.cookie_jar)
                dataq = []
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
                    'http://localhost:8000/shares/?method=updateshared&ccid='
                    + self.ccid + "&name=" + os.path.basename(s[3]) + "&fileid=" + s[2] ,
                    headers,
                    body)
                d.addCallback(self.printPutReply_cb)

                return NOT_DONE_YET

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
            if s[1] == "shared":
                return updateShared_cb(new_iv)
            return updateFile_cb(new_iv)


        hsmd_data = (encryptFile_cb, s[2])
        if s[1] == "file":
            return self.handleGetFileMData(hsmd_data)
        return self.handleGetShareMData(hsmd_data)

    def handleUpdateSharePerm(self, s):
        self.processCookie("/shares")
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        headers = http_headers.Headers()
        d = agent.request(
            'POST',
            'http://localhost:8000/shares/?method=updateshareperm&ccid='
            + self.ccid + "&rccid=" + s[3] + "&fileid=" + s[2] + "&writeable=" + s[4] ,
            headers,
            None)
        d.addCallback(self.printPutReply_cb)

        return NOT_DONE_YET

#Delete Operaions
#
    # handleDelete: handles delete commands
    def handleDelete(self, line):
        def printDeleteReply_cb(data):
            if not data:
                print "Done."
            else:
                pprint(data)

        def deleteFile_cb():
            self.processCookie("/files")
            agent = CookieAgent(Agent(reactor), self.cookie_jar)
            headers = http_headers.Headers()
            d = agent.request(
                'DELETE',
                'http://localhost:8000/files/?method=delete&ccid='
                + self.ccid + "&fileid=" + s[2],
                headers,
                None)

            d.addCallback(printDeleteReply_cb)

        def deleteShare_cb():
            self.processCookie("/shares")
            agent = CookieAgent(Agent(reactor), self.cookie_jar)
            headers = http_headers.Headers()
            d = agent.request(
                'DELETE',
                'http://localhost:8000/shares/?method=delete&ccid='
                + self.ccid + "&fileid=" + s[2] + "&rccid=" + s[3],
                headers,
                None)

            d.addCallback(printDeleteReply_cb)

        s = line.split()
        if len(s) == 4:
            return deleteShare_cb()
        if len(s) == 3:
            return deleteFile_cb()

        print "Error: invalid arguments!\n"
        print "Usage: delete <file|share> <fileid> <None|rccid>"
        return


# Share Operation
#
    def handleShare(self, line):

        def getFKey_cb(data):
            enc_key = data["data"]["SymKey"]

            def getDstKey_cb(data):
                dstkey = data["data"]["PubKey"]
                print "pubkey" + dstkey

                def shareFile_cb():
                    self.processCookie("/shares")
                    agent = CookieAgent(Agent(reactor), self.cookie_jar)
                    dataq = []
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
                return shareFile_cb()



            hfmd_data = (getDstKey_cb, s[3].lower())
            return self.handleGetMData(hfmd_data)

        s = line.split()
        if len(s) == 4:
            hmd_data = (getFKey_cb, s[2].lower())
            return self.handleGetFileMData(hmd_data)

        else:
            if s[1].lower() != "file":
                print "Error: invalid arguments!\n"
                print "Usage: share file <fileid> <recipient's ccid>"
                return
