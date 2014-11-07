from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from twisted.protocols.basic import FileSender

from twisted.web.client import FileBodyProducer
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from pprint import pformat

class BeginningPrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10

    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            print 'Some data received:'
            print display
            self.remaining -= len(display)

    def connectionLost(self, reason):
        print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(None)

# class fileSendWrap(FileSender):
#     def __init__(self,file):
#         self.file = file

#     def startProducing(cons):
#         beginFileTransfer(self, file, cons)

class SaveContents(Protocol):
    def __init__(self, finished, filesize, filename):
        self.finished = finished
        self.remaining = filesize
        self.outfile = open(filename, 'wb')

    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            self.outfile.write(display)
            self.remaining -= len(display)
        else:
            self.outfile.close()

    def connectionLost(self, reason):
        print 'Finished receiving body:', reason.getErrorMessage()
        self.outfile.close()
        self.finished.callback(None)

agent = Agent(reactor)
f = open('recfile.exe', 'rb')
body = FileBodyProducer(f)
d = agent.request(
    'PUT',
    'http://localhost:8000/files/?method=putfile&pboxid=1&name=test.txt',
    Headers({'User-Agent': ['Twisted Web Client Example'],
             'Content-Type': ['multipart/form-data; boundary=1024'.format()]}),
    body)

def cbRequest(response):
    print 'Response version:', response.version
    print 'Response code:', response.code
    print 'Response phrase:', response.phrase
    print 'Response headers:'
    print 'Response length:', response.length
    print pformat(list(response.headers.getAllRawHeaders()))
    finished = Deferred()
    response.deliverBody(SaveContents(finished, response.length, 'test2.pdf'))
    return finished
d.addCallback(cbRequest)

def cbShutdown(ignored):
    file.close()
    reactor.stop()
d.addBoth(cbShutdown)

reactor.run()
