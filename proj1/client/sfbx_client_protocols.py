#from twisted.internet.defer import Deferred
#from zope.interface import implements
from StringIO import StringIO

from twisted.internet.protocol import Protocol

class FileDownload(Protocol):

    def __init__(self, finished, cons):
       self.finished = finished
       self.cons = cons

    def dataReceived(self, data):
        print 'Some data received:'
        print data
        self.cons.write(data)

    def connectionMade(self):
        self.cons.registerProducer(self, streaming=True)

    def connectionLost(self, reason):
        self.cons.unregisterProducer()
        print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(None)
