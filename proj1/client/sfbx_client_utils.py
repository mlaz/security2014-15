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

from sfbx_client_cryptography import ClientIdentity
from sfbx_client_cryptography import getTicket
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
            # print 'Response version:', response.version
            # print 'Response code:', response.code
            # print 'Response phrase:', response.phrase
            # print 'Response headers:'
            # print pformat(list(response.headers.getAllRawHeaders()))
            defer = Deferred()
            defer.addCallback(method)
            response.deliverBody(getKey(defer))
            return NOT_DONE_YET

        agent = Agent(reactor)
        d = agent.request(
                    'GET',
                    'http://localhost:8000/session/?method=getkey',
                    Headers({'User-Agent': ['Twisted Web Client Example'],
                    'Content-Type': ['text/x-greeting']}),
                    None)

        d.addCallback(handleGetKey_cb)

        return NOT_DONE_YET

    # handleGetTicket: handles getticket operations
    def handleGetTicket(self, method):
        def handleGetTicket_cb(response):
            # print 'Response version: ', response.version
            # print 'Response code: ', response.code
            # print 'Response phrase: ', response.phrase
            # print 'Response headers: '
            # print pformat(list(response.headers.getAllRawHeaders()))
            defer = Deferred()
            defer.addCallback(method)
            response.deliverBody(getTicket(defer, self.client_id))
            return NOT_DONE_YET

        agent = Agent(reactor)
        d = agent.request(
                'GET',
                'http://localhost:8000/session/?method=getticket&ccid='+ self.ccid,
                Headers({'User-Agent': ['Twisted Web Client Example'],
                'Content-Type': ['text/x-greeting']}),
                None)

        d.addCallback(handleGetTicket_cb)

        return NOT_DONE_YET

    # handleRegister: Handles register commands.
    def handleRegister(self, name):

        agent = Agent(reactor)
        body = FileBodyProducer(StringIO(self.client_id.pub_key.exportKey('PEM')))
        d = agent.request(
            'PUT',
            'http://localhost:8000/pboxes/?method=register&ccid='+ self.ccid
            + '&name=' + name,
            Headers({'User-Agent': ['Twisted Web Client Example'],
                     'Content-Type': ['text/x-greeting']}),
            body)

        return NOT_DONE_YET

    # handleList: handles every list command
    def handleList(self, line):
        def handleList_cb(response):
            # print 'Response version:', response.version
            # print 'Response code:', response.code
            # print 'Response phrase:', response.phrase
            # print 'Response headers:'
            # print pformat(list(response.headers.getAllRawHeaders()))
            defer = Deferred()
            response.deliverBody(BeginningPrinter(defer))
            return NOT_DONE_YET

        def handleListPboxes(signedTicket):
            print len(signedTicket)
            agent = Agent(reactor)
	    body = FileBodyProducer(StringIO(signedTicket))
            d = agent.request(
                    'GET',
                    'http://localhost:8000/pboxes/?method=list&ccid=' + self.ccid,
                    Headers({'User-Agent': ['Twisted Web Client Example'],
                    'Content-Type': ['text/x-greeting']}),
                    body)
            d.addCallback(handleList_cb)
            return NOT_DONE_YET

        def handleListFiles(signedTicket):
            agent = Agent(reactor)
            body = FileBodyProducer(StringIO(signedTicket))
	    d = agent.request(
                    'GET',
                    'http://localhost:8000/files/?method=list&ccid=' + self.ccid,
                    Headers({'User-Agent': ['Twisted Web Client Example'],
                    'Content-Type': ['text/x-greeting']}),
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

    # handleGet
    def handleGet(self, line):
        def printResult_cb(data):
            # print 'Response version:', response.version
            # print 'Response code:', response.code
            # print 'Response phrase:', response.phrase
            # print 'Response headers:'
            # print pformat(list(response.headers.getAllRawHeaders()))
            pprint(data) #TODO: Format this!
            return NOT_DONE_YET

        def handleGet_cb(ticket):
            s = line.split()
            if s[1].lower() == "pboxinfo":
                return self.handleGetMData(printResult_cb, ticket, s[2].lower())

        def handleGetFile(signedTicket):
            def handleGetFile_cb(response, f):
                finished = Deferred()
                cons = FileConsumer(f)
                response.deliverBody(FileDownload(finished, cons))
                return finished

            agent = Agent(reactor)
            body = FileBodyProducer(StringIO(signedTicket))
            d = agent.request(
                    'GET',
                    'http://localhost:8000/files/?method=getfile&ccid=' + self.ccid + '&fileid=' + fileId,
                    Headers({'User-Agent': ['Twisted Web Client Example'],
                             'Content-Type': ['text/x-greeting']}),
                    body)
            f = open(fileId, "w")
            d.addCallback(handleGetFile_cb, f)
            return NOT_DONE_YET

        s = line.split()
        if len(s) == 2:
            if s[1].lower() == "pboxinfo":
                return self.handleGetTicket(handleGet_cb)
            elif s[1].lower() == "files":
	        return self.handleGetTicket(handleListFiles)
	    else:
		print "Error: invalid arguments!\n"
		print "Correct usage: get <pboxinfo|file>"
        elif len(s) == 3:
            if s[1].lower() == "file":
                fileId = s[2]
                return self.handleGetTicket(handleGetFile)
            else:
                print "Error: invalid arguments!\n"
                print "Correct usage: get file <fileId>"
        else:
	    print "Error: invalid arguments!\n"
            print "Correct usage: list <pboxes|files> or list file <fileId>"


    # handleGetMData: Handles get pbox metadata operations.
    def handleGetMData(self, method, ticket, tgtccid):
        def handleGetMData_cb(response):
            defer = Deferred()
            defer.addCallback(method)
            response.deliverBody(getMData(defer))
            return NOT_DONE_YET

        agent = Agent(reactor)
        body = FileBodyProducer(StringIO(ticket))
        d = agent.request(
			'GET',
            'http://localhost:8000/pboxes/?method=get_mdata&ccid='
            + self.ccid + "&tgtccid=" + tgtccid,
            Headers({'User-Agent': ['Twisted Web Client Example'],
            'Content-Type': ['text/x-greeting']}),
            body)

        d.addCallback(handleGetMData_cb)

        return NOT_DONE_YET



    # handleGetFile:
    def handleGetFile(self, line):
        # def handleGet_cb(response, file):
        #     print 'Response version:', response.version
        #     print 'Response code:', response.code
        #     print 'Response phrase:', response.phrase
        #     print 'Response headers:'
        #     print pformat(list(response.headers.getAllRawHeaders()))
        #     defer = Deferred()
        #     cons = FileConsumer(file)
        #     response.deliverBody(FileDownload(defer, cons))
        #     return NOT_DONE_YET


        # agent = Agent(reactor)
        # s = line.split()
        # if len(s) != 3:
        #     print "Error: invalid arguments!\n"
        #     return
        # else:
        #     if s[1].lower() != "file":
        #         print "Error: invalid arguments!\n"
        #         print "Correct usage: get file <fileId>"
        #     elif s[1].lower() == "file":
        #         fileId = s[2].lower()
        #         file = open(fileId, "w")
        #         d = agent.request(
        #                 'GET',
        #                 'http://localhost:8000/files/?method=getfile&fileid='+ fileId +'&pboxid=1',
        #                 Headers({'User-Agent': ['Twisted Web Client Example'],
        #                 'Content-Type': ['text/x-greeting']}),
        #                 None)

        #     d.addCallback(handleGet_cb, file)
        return NOT_DONE_YET

    # handlePutFile:
    def handlePutFile(self, line):
        def printPutReply_cb(response):
            print "FINISHED"

            defer = Deferred()
            response.deliverBody(getMData(defer))
            return NOT_DONE_YET

        def putFile_cb(ticket):
            print "HERE!!!!"
            s = line.split()
            file = open(s[2], 'r')
            agent = Agent(reactor)
            body = _FileProducer(file ,ticket)
            headers = http_headers.Headers()
            d = agent.request(
                'PUT',
                'http://localhost:8000/files/?method=putfile&ccid='
                + self.ccid + "&name=" + os.path.basename(s[2]),
                headers,
                body)
            d.addCallback(printPutReply_cb)

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


    def handleUpdate(self, line):
        return

    def handleDelete(self, line):
        return
