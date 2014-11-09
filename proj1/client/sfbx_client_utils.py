from twisted.internet import reactor
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers
from twisted.web.server import NOT_DONE_YET
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.protocols.ftp import FileConsumer
from StringIO import StringIO
from pprint import pformat
from pprint import pprint
import json

class FileDownload(Protocol):
    def __init__(self, finished, cons):
        self.finished = finished
        self.cons = cons
        
    def dataReceived(self, data):
        self.cons.write(data)
        
    def connectionMade(self):
        self.cons.registerProducer(self, streaming=True)
        
    def connectionLost(self, reason):
        self.cons.unregisterProducer()
        print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(None)

class BeginningPrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.total_response = ""

    def dataReceived(self, bytes):
        self.total_response += bytes
            
    def connectionLost(self, reason):
        print 'Response:\n', formatResponse(self.total_response)
        print 'Finished receiving body: ', reason.getErrorMessage()

def formatResponse(response):
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

class SafeBoxClient():
    def __init__(self):
        self.server = "localhost:8000"

    def handleList(self, line):
        def handleList_cb(response):
            print 'Response version:', response.version
            print 'Response code:', response.code
            print 'Response phrase:', response.phrase
            print 'Response headers:'
            print pformat(list(response.headers.getAllRawHeaders()))
            defer = Deferred()
            #defer.addCallback(handle_result)
            response.deliverBody(BeginningPrinter(defer))
            return NOT_DONE_YET
            #return defer

        agent = Agent(reactor)
        s = line.split()
        if s[1].lower() == "pboxes":
            d = agent.request(
                    'GET',
                    'http://localhost:8000/pboxes/?method=list',
                    Headers({'User-Agent': ['Twisted Web Client Example'],
                    'Content-Type': ['text/x-greeting']}),
                    None)

        elif s[1].lower() == "files":
            d = agent.request(
                    'GET',
                    'http://localhost:8000/files/?method=list&pboxid=1',
                    Headers({'User-Agent': ['Twisted Web Client Example'],
                    'Content-Type': ['text/x-greeting']}),
                    None)

        d.addCallback(handleList_cb)

        return NOT_DONE_YET

    def handleGet(self, line):
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
        if s[1].lower() == "file":
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