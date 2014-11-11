from twisted.internet import reactor
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers
from twisted.internet import abstract
from twisted.web.server import NOT_DONE_YET
from twisted.web import iweb
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.protocols.ftp import FileConsumer
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

#
class SafeBoxClient():
    def __init__(self, server_addr="localhost:8000"):
        self.server_addr = server_addr
        self.client_id = self.ccid = self.ccid = None

    #initializes the client's remaining attributes
    def startClient(self, ccid, passwd, name):

        # checking if client is already registered
        def checkClientReg_cb(ticket):
            if ticket is None:
                print "user not registered!"
                if name is "":
                    print "Please provide your name for registry."
            else:
                print "Welcome!"

        # Instanciating ClientIdentity
        def startClientId_cb(key):
            self.client_id = ClientIdentity(self.ccid, passwd, key)
            self.handleGetTicket(checkClientReg_cb)

        self.ccid = ccid
        return self.handleGetKey(startClientId_cb)


    # handleGetKey: handles getkey operations
    def handleGetKey(self, method):
        def handleGetKey_cb(response):
            print 'Response version:', response.version
            print 'Response code:', response.code
            print 'Response phrase:', response.phrase
            print 'Response headers:'
            print pformat(list(response.headers.getAllRawHeaders()))
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
            print 'Response version: ', response.version
            print 'Response code: ', response.code
            print 'Response phrase: ', response.phrase
            print 'Response headers: '
            print pformat(list(response.headers.getAllRawHeaders()))
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


    def handleGetMData(self, method):
        def handleGetMData_cb(response):
            print 'Response version: ', response.version
            print 'Response code: ', response.code
            print 'Response phrase: ', response.phrase
            print 'Response headers: '
            print pformat(list(response.headers.getAllRawHeaders()))
            defer = Deferred()
            defer.addCallback(self)
            response.deliverBody(getMData(defer))
            return NOT_DONE_YET

        agent = Agent(reactor)
        d = agent.request(
			'GET',
            'http://localhost:8000/pboxes/?method=get_mdata&ccid=' + self.ccid,
            Headers({'User-Agent': ['Twisted Web Client Example'],
            'Content-Type': ['text/x-greeting']}),
            None)

        d.addCallback(handleGetMData_cb)

        return NOT_DONE_YET


    # handleRegister: Handles register commands.
    def handleRegister(self, line):
        def handleRegister_cb(response):
            return NOT_DONE_YET

        agent = Agent(reactor)
        s = line.split()
        if len(s) != 4:
            print "Error: invalid arguments\n"
            print "Correct usage: register <username> <ccnumber> <password>"
            return
        else:
            username = s[1]
            self.ccid = s[2]
            self.passwd = s[3]



            body = FileBodyProducer(StringIO(ci.pub_key.exportKey('PEM')))
            d = agent.request(
                        'PUT',
                        'http://localhost:8000/pboxes/?method=register&ccid='+ ccnumber +'&name=' + username,
                        Headers({'User-Agent': ['Twisted Web Client Example'],
                        'Content-Type': ['text/x-greeting']}),
                        body)

            d.addCallback(handleRegister_cb)
            return NOT_DONE_YET

    # def handleLogin(self, line):
    #     s = line.split()
    #     if len(s) != 3:
    #         print "Error: invalid arguments\n"
    #         print "Correct usage: login <CCnumber> <password>"
    #         return
    #     else:
    #         self.ccid = s[1]
    #         self.passwd = s[2]
    #         print "Login sucessful"
    #         return self.handleGetKey()

    # handleList: handles every list command
    def handleList(self, line):
        def handleList_cb(response):
            print 'Response version:', response.version
            print 'Response code:', response.code
            print 'Response phrase:', response.phrase
            print 'Response headers:'
            print pformat(list(response.headers.getAllRawHeaders()))
            defer = Deferred()
            response.deliverBody(BeginningPrinter(defer))
            return NOT_DONE_YET

        def handleListPboxes(signedTicket):
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

        return NOT_DONE_YET

    # handleGetFile:
    def handleGetFile(self, line):
        def handleGet_cb(response, file):
            print 'Response version:', response.version
            print 'Response code:', response.code
            print 'Response phrase:', response.phrase
            print 'Response headers:'
            print pformat(list(response.headers.getAllRawHeaders()))
            defer = Deferred()
            cons = FileConsumer(file)
            response.deliverBody(FileDownload(defer, cons))
            return NOT_DONE_YET


        agent = Agent(reactor)
        s = line.split()
        if len(s) != 3:
            print "Error: invalid arguments!\n"
            return
        else:
            if s[1].lower() != "file":
                print "Error: invalid arguments!\n"
                print "Correct usage: get file <fileId>"
            elif s[1].lower() == "file":
                fileId = s[2].lower()
                file = open(fileId, "w")
                d = agent.request(
                        'GET',
                        'http://localhost:8000/files/?method=getfile&fileid='+ fileId +'&pboxid=1',
                        Headers({'User-Agent': ['Twisted Web Client Example'],
                        'Content-Type': ['text/x-greeting']}),
                        None)

            d.addCallback(handleGet_cb, file)

            return NOT_DONE_YET

    def handlePut(self, line):
        return

    def handleUpdate(self, line):
        return

    def handleDelete(self, line):
        return

### Helper functions: mostly for formatting
    def formatResponse(response):
        response = json.dumps(response)
        pprint(response)
        response = json.loads(response, object_hook=_decode_dict)
        if (response["status"] == ["error"]):
            print(response["error"])
        else:
            for elem in response["list"].keys():
                for attr in response["list"].get(elem):
                    print attr, ": ", response["list"].get(elem).get(attr)

    def _decode_list(data):
        rv = []
        for item in data:
            if isinstance(item, unicode):
                item = item.encode('utf-8')
            elif isinstance(item, list):
                item = _decode_list(item)
            elif isinstance(item, dict):
                item = _decode_dict(item)
                rv.append(item)
        return rv

    def _decode_dict(data):
        rv = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            elif isinstance(value, list):
                value = _decode_list(value)
            elif isinstance(value, dict):
                value = _decode_dict(value)
                rv[key] = value
        return rv

    def handle_result(response):
        print " "
