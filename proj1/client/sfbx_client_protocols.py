from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol

from base64 import b64encode, b64decode
from pprint import pprint
from StringIO import StringIO
import json

from sfbx_decode_utils import DecodeUtils

# FileDownload:
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
        print 'Response:\n', self.formatResponse(self.total_response)
        print 'Finished receiving body: ', reason.getErrorMessage()

    def formatResponse(self, response):
        #response = json.dumps(response)
        #pprint(response)
        #response = json.loads(response, object_hook=_decode_dict)
        response = json.loads(response)
        if (response["status"] == ["error"]):
            print(response["error"])
        else:
            for elem in response["list"].keys():
                for attr in response["list"].get(elem):
                    print attr, ": ", response["list"].get(elem).get(attr)

class getKey(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.total_response = ""

    def dataReceived(self, bytes):
        self.total_response += bytes

    def connectionLost(self, reason):
        data = self.formatKey(self.total_response)
        print 'The key is:\n', data
        self.finished.callback(data)

    def formatKey(self, response):
        response = json.loads(response)
        #response = json.loads(response, object_hook=du.decode_dict)
        if (response["status"] == ["error"]):
            return (response["error"])
        else:
            return (response["key"])

class getMData(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.total_response = ""

    def dataReceived(self, bytes):
        self.total_response += bytes

    def connectionLost(self, reason):
        print 'User Data:\n', formatMData(self.total_response)

    def formatMData(response):
        response = json.loads(response)
        #response = json.loads(response, object_hook=du.decode_dict)
        if (response["status"] == ["error"]):
            print(response["error"])
        else:
            s = response["data"]
            #s = s.strip("(")
            #s = s.strip(")")
            #s = s.strip(",")
            #s = s.strip('"')
            print s

du = DecodeUtils()
