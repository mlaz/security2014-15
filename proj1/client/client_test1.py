import random
import StringIO
import os
from zope import interface

from twisted.internet import abstract, defer, reactor
from twisted.web import client, http_headers, iweb


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
        """
        Starts producing to the given consumer.
        """
        print "START"
        self._consumer = consumer
        self._deferred = defer.Deferred()
        reactor.callLater(0, self._produceSome)
        return self._deferred

    def _scheduleSomeProducing(self):
        """
        Schedules some producing.
        """
        self._delayedProduce = reactor.callLater(0, self._produceSome)

    def _produceSome(self):
        """
        Reads some data from the file synchronously, writes it to the
        consumer, and cooperatively schedules the next read. If no data is
        left, fires the deferred and loses the reference to it.

        If paused, does nothing.
        """
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
        """
        Pauses the producer.
        """
        print "PAUSE"
        self._paused = True
        if self._delayedProduce is not None:
            self._delayedProduce.cancel()

    def resumeProducing(self):
        """
        Unpauses the producer.
        """
        print "RESUME"
        self._paused = False
        if self._deferred is not None:
            self._scheduleSomeProducing()

    def stopProducing(self):
        """
        Loses a reference to the deferred.
        """
        print "STOP"
        if self._delayedProduce is not None:
            self._delayedProduce.cancel()
        self._deferred = None

if __name__ == "__main__":

    def cb(ignored):
        print "FINISHED"
        file.close()
        reactor.stop()

    file = open('recfile.exe', 'rb')
    producer = _FileProducer(file)
    headers = http_headers.Headers()

    agent = client.Agent(reactor)
    df = agent.request("PUT", "http://localhost:8000/files/?method=putfile&name=sfsd", headers, producer)
    df.addCallback(cb)
    reactor.run()
