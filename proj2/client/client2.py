from pprint import pformat

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from twisted.protocols.ftp import FileConsumer
from sfbx_client_protocols import FileDownload
#get file#
def cbRequest(response, file):
    print 'Response version:', response.version
    print 'Response code:', response.code
    print 'Response phrase:', response.phrase
    print 'Response headers:'
    print pformat(list(response.headers.getAllRawHeaders()))
    finished = Deferred()
    cons = FileConsumer(file)
    response.deliverBody(FileDownload(finished, cons))
    return finished

def cbShutdown(ignored, file):
    file.close();
    reactor.stop()

def main():
    file = open("recfile.exe", "w")

    agent = Agent(reactor)
    d = agent.request(
        'GET',
        'http://localhost:8000/files/?method=getfile&pboxid=1&fileid=1',
        Headers({'User-Agent': ['Twisted Web Client Example'],
                 'Content-Type': ['text/x-greeting']}),
        None)

    d.addCallback(cbRequest, file)
    d.addBoth(cbShutdown, file)

    reactor.run()

if __name__ == "__main__":
    main()
