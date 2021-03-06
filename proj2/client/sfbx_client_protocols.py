from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol

from base64 import b64encode, b64decode
from pprint import pprint
from StringIO import StringIO
import json

from sfbx_decode_utils import *
from sfbx_client_cryptography import IV_KEY_SIZE_B64

# FileDownload:
class FileDownload(Protocol):
    def __init__(self, finished, cons):
        self.finished = finished
        self.cons = cons
        self.total = 0

    def dataReceived(self, data):
        if self.total >= (2 * IV_KEY_SIZE_B64):
            self.cons.write(data) #b64decode
        else:
            self.cons.write(data)
        self.total = self.total + len(data)

    def connectionMade(self):
        self.cons.registerProducer(self, streaming=True)

    def connectionLost(self, reason):
        self.cons.unregisterProducer()
        #print 'Finished receiving body: ', reason.getErrorMessage()
        self.finished.callback(None)

# DataPrinter:
class DataPrinter(Protocol):
    def __init__(self, finished, method):
        self.finished = finished
        self.total_response = ""
        self.method = method

    def dataReceived(self, bytes):
        self.total_response += bytes

    def connectionLost(self, reason):
        data = self.formatResponse(self.total_response)
        #print 'Response:\n', data
        self.finished.callback(data)
        #print 'Finished receiving body: ', reason.getErrorMessage()

    def formatResponse(self, response):
        response = json.loads(response)
        if self.method == "list":
            if (response["status"] == ["error"]):
                print(response["error"])
	    else:
		for elem in response["list"].keys():
		    for attr in response["list"].get(elem):
			print attr, ": ", response["list"].get(elem).get(attr)
	elif self.method == "getkey":
	    if (response["status"] == ["error"]):
	        return (response["error"])
	    else:
		return (response["key"])
	elif self.method == "getmdata":
	    if (response["status"] != "OK"):
		data = response["status"]["message"]
	    else:
		data = response
	    return data
        elif self.method == "bool":
            if (response["status"] != "OK"):
                data = False
            else:
                data = True
            return data
