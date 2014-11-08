import random
import StringIO
import os
from zope import interface

from twisted.internet import abstract, defer, reactor
from twisted.web import client, http_headers, iweb

# The file test.mp3 was used for testing this module during development
# it's at the files resource for this project on code.ua.pt

class _FileProducer(object):  # pragma: no cover
    """
    A simple producer that produces a body.
    """
    interface.implements(iweb.IBodyProducer)

    def __init__(self, file, chunksize=200):
        self._file = file
        self._consumer = self._deferred = self._delayedProduce = None
        self._paused = False
        self.chunksize = chunksize
        self.length = iweb.UNKNOWN_LENGTH

    def startProducing(self, consumer):
        print "START"
        self._consumer = consumer
        self._deferred = defer.Deferred()
        reactor.callLater(0, self._produceSome)
        return self._deferred

    def _scheduleSomeProducing(self):
        self._delayedProduce = reactor.callLater(0, self._produceSome)

    def _produceSome(self):
        if self._paused:
            return

        data = self._file.read(self.chunksize)
        if data:
            self._consumer.write(data)
            self._scheduleSomeProducing()
        else:
            print "FINISHED0"
            if self._deferred is not None:
                print "FINISHED0"
                self._deferred.callback(None)
                self._deferred = None

    def pauseProducing(self):
        print "PAUSE"
        self._paused = True
        if self._delayedProduce is not None:
            self._delayedProduce.cancel()

    def resumeProducing(self):
        print "RESUME"
        self._paused = False
        if self._deferred is not None:
            self._scheduleSomeProducing()

    def stopProducing(self):
        print "STOP"
        if self._delayedProduce is not None:
            self._delayedProduce.cancel()
        self._deferred = None

if __name__ == "__main__":

    def cb(ignored):
        print "FINISHED"
        file.close()
        reactor.stop()

    file = open('recfile', 'rb')
    producer = _FileProducer(file)
    headers = http_headers.Headers()

    agent = client.Agent(reactor)
    df = agent.request(
        "PUT",
        "http://localhost:8000/files/?method=putfile&pboxid=1&name=PinkFloyd&iv=12345&key=54321",
        headers, producer)
    df.addCallback(cb)
    reactor.run()
