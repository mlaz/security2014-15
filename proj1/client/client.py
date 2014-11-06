from pprint import pformat

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from sfbx_client_protocols import FileDownload

def cbRequest(response, file):
    print 'Response version:', response.version
    print 'Response code:', response.code
    print 'Response phrase:', response.phrase
    print 'Response headers:'
    print pformat(list(response.headers.getAllRawHeaders()))
    finished = Deferred()
    response.deliverBody(FileDownload(finished))
    return finished

def cbShutdown(ignored, file):
    file.close();
    reactor.stop()

def main():
    file = open("recfile.exe", "w")

    agent = Agent(reactor)
    d = agent.request(
        'GET',
        'http://localhost:8000/files/?method=getfile&fileid=1',
        Headers({'User-Agent': ['Twisted Web Client Example'],
                 'Content-Type': ['text/x-greeting']}),
        None)

    d.addCallback(cbRequest, file)
    d.addBoth(cbShutdown, file)

    reactor.run()

if __name__ == "__main__":
    main()
