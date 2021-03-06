import random
from StringIO import StringIO
import os
from zope import interface

from twisted.internet import abstract, defer, reactor
from twisted.web import client, http_headers, iweb

from sfbx_fs_utils import _FileProducer


# The file test.mp3 was used for testing this module during development
# it's at the files resource for this project on code.ua.pt

# class _FileProducer(object):
#     interface.implements(iweb.IBodyProducer)

#     def __init__(self, file, ticket=None):
#         self._file = file
#         self._consumer = self._deferred = self._delayedProduce = None
#         self._paused = False
#         self.chunksize = CHUNK_SIZE
#         self.length = iweb.UNKNOWN_LENGTH
#         self.ticket = ticket

#     def startProducing(self, consumer):
#         print "START"
#         self._consumer = consumer
#         self._deferred = defer.Deferred()
#         reactor.callLater(0, self._produceSome)
#         return self._deferred

#     def _scheduleSomeProducing(self):
#         self._delayedProduce = reactor.callLater(0, self._produceSome)

#     def _produceSome(self):
#         if self._paused:
#             return

#         if self.ticket is None:
#             data = self._file.read(self.chunksize)
#         else:
#             data = StringIO(self.ticket).read(self.chunksize)
#             self.ticket = None
#         if data:
#             self._consumer.write(data)
#             self._scheduleSomeProducing()
#         else:
#             print "FINISHED0"
#             if self._deferred is not None:
#                 print "FINISHED0"
#                 self._deferred.callback(None)
#                 self._deferred = None

#     def pauseProducing(self):
#         print "PAUSE"
#         self._paused = True
#         if self._delayedProduce is not None:
#             self._delayedProduce.cancel()

#     def resumeProducing(self):
#         print "RESUME"
#         self._paused = False
#         if self._deferred is not None:
#             self._scheduleSomeProducing()

#     def stopProducing(self):
#         print "STOP"
#         if self._delayedProduce is not None:
#             self._delayedProduce.cancel()
#         self._deferred = None

if __name__ == "__main__":
    ticket = "I AM A VERYVERY LOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOONG STRING"

    def cb(ignored):
        print "FINISHED"
        file.read(20)
        reactor.stop()

    file = open('recfile.exe', 'rb')
    producer = _FileProducer(file, ticket)
    headers = http_headers.Headers()

    agent = client.Agent(reactor)
    df = agent.request(
        "PUT",
        "http://localhost:8000/files/?method=putfile&ccid=111222333&name=file.txt&iv=12345&key=54321",
        headers, producer)
    df.addCallback(cb)
    reactor.run()
