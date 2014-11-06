#from twisted.internet.defer import Deferred
#from zope.interface import implements
from StringIO import StringIO

from twisted.internet.protocol import Protocol

class FileDownload(Protocol):

    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10
        self.data = StringIO()

    def dataReceived(self, bytes):
        display = bytes[:self.remaining]
        if self.remaining:
            print 'Some data received:'
            print display
            self.remaining -= len(display)

    def connectionLost(self, reason):
        print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(None)
