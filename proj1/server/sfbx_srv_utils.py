from twisted.enterprise import adbapi
from twisted.protocols.basic import FileSender
from twisted.python.log import err
from twisted.web.server import NOT_DONE_YET
from twisted.internet import abstract, defer, reactor
from twisted.web import iweb
from twisted.protocols.ftp import FileConsumer

from zope import interface
from pprint import pprint

import json


dbfilename = "safebox.sqlite"
dbpool = adbapi.ConnectionPool("sqlite3", dbfilename, check_same_thread=False)

#
# SafeBox server utilities API
#

# PBox related operations:
#

# listPBoxes(): Queries for all entries on PBox's basic meta-data attributes.
def listPBoxes():
    return dbpool.runQuery("SELECT PBoxId, UserCCId, UserName FROM PBox")

# listPBoxes_cb(): Callback for listPBoxes(), processes retrieved data for reply.
def listPBoxes_cb(data, request):
    data_dict = {}

    tsize = 0
    for row in data:
        row_dict = {
            'PBoxId': row[0],
            'UserCCId': row[1],
            'UserName': row[2] }
        data_dict.update({tsize: row_dict})
        tsize = tsize + 1

    reply_dict = { 'status': "OK", 'size': tsize, 'list': data_dict }
    request.write(json.dumps(reply_dict, encoding="utf-8"));
    request.finish()

# getPBoxMData(): Queries the data base for all entries on all PBox's attributes for given ccid.
def getPBoxMData(args):
    ccid_str = str(args['ccid'])
    ccid_str = strip_text(ccid_str)

    return dbpool.runQuery(
        "SELECT * FROM PBox WHERE UserCCId = ?", (ccid_str,))

# getPBoxMData_cb(): Callback for getPBoxMData(), Processes retrieved data for reply.
def getPBoxMData_cb (data, request):
    reply_dict = {}

    for row in data:
        row_dict = {
            'PBoxId': row[0],
            'UserCCId': row[1],
            'UserName': row[2],
            'PubKey': row[3],}
        reply_dict.update(row_dict)

    reply_dict = {'status': "OK", 'data': reply_dict}
    request.write(json.dumps(reply_dict, encoding="utf-8"));
    request.finish()

# registerPBox(): Inserts a new entry on PBox table.
def registerPBox(args):
    ccid = str(args['ccid'])
    ccid = strip_text(ccid)
    name = str(args['name'])
    name = strip_text(name)
    pubkey = str(args['pubkey'])
    pubkey = strip_text(pubkey)


    return dbpool.runQuery(
        "INSERT INTO PBox (UserCCId, UserName, PubKey) VALUES (?, ?, ?) ", (ccid, name, pubkey));

# registerPBox_cb(): Callback for registerPBox(), produces reply according to registerPBox return value.
def registerPBox_cb (data, request):
    if len(data) == 0:
        reply_dict = {'status': "OK"}

    else:
        reply_dict = { 'status': {'error': "Unsuccessful db transaction", 'message': data} }
    request.write(json.dumps(reply_dict, encoding="utf-8"));
    request.finish()

# File related operations:
#

# listFiles(): Retrieves FileName and FileId attributes for a given pboxid.
def listFiles(args):
    pboxid = str(args['pboxid'])
    pboxid = strip_text(pboxid)

    return dbpool.runQuery(
        "SELECT FileName, FileId FROM File WHERE OwnerPBoxId = ?", (pboxid,));

# listFiles_cb(): Callback for listFiles(), produces the reply from the database query result.
def listFiles_cb (data, request):
    data_dict = {}

    tsize = 0
    for row in data:
        row_dict = {
            'FileName': row[0],
            'FileId': row[1]}
        data_dict.update({tsize: row_dict})
        tsize = tsize + 1

    reply_dict = { 'status': "OK", 'size': tsize, 'list': data_dict }
    request.write(json.dumps(reply_dict, encoding="utf-8"));
    request.finish()

# returnFile(): Retrieves metadata for a given fileid.
def getFileInfo(args):
    fileid = str(args['fileid'])
    fileid = strip_text(fileid)

    return dbpool.runQuery(
        "SELECT * FROM File WHERE FileId = ?", (fileid,));

# retGetFile_cb(): Callback for registerPBox(), sends the file back to the client.
def retGetFile_cb (data, request):

    #TODO: Implement infrastructure for ownership checking (add field)
    # path = <OwnerPBoxId>/<FileId>
    file = open(str(data[0][1]) + "/" + str(data[0][0]) ,"r")
    sender = FileSender()
    sender.CHUNK_SIZE = 200
    df = sender.beginFileTransfer(file, request)

    def finishTrnf_cb(ignored):
        file.close()
        request.finish()

    df.addErrback(err)
    df.addCallback(finishTrnf_cb)
    return NOT_DONE_YET

# handlePutFile(): This is done in 3 steps:
# 1 - Inserts entry on the Files table;
# 2 - Queries for the new file's Id;
# 3 - Write file to disk
def handlePutFile(request):
#    pprint(request.__dict__)

    def finishRequest(ignore,file):
        file.close()
        request.finish()

    # TODO: we shouf try a way of rollback
    #  if anything goes wrong at this point
    # This method should start writing the file to the disk.
    def writeFile(data):
        pboxid = str(request.args['pboxid'])
        pboxid = strip_text(pboxid)
        # path = <OwnerPBoxId>/<FileId>
        file = open(pboxid + "/" + str(data[0][0]) ,"w")
        prod = FD2FileProducer(request)
        cons = FileConsumer(file)
        cons.registerProducer(prod, True)
        d = prod.startProducing(cons)
        d.addCallback(finishRequest, file)

        return NOT_DONE_YET

    # This query should retreive the highest file number for a given pboxid
    def getFilePath(data):
        pboxid = str(request.args['pboxid'])
        pboxid = strip_text(pboxid)
        d = dbpool.runQuery(
            "SELECT FileId " +
            "FROM File " +
            "WHERE OwnerPBoxId = ? " +
            "ORDER BY FileId DESC",
            (pboxid,))
        d.addCallback(writeFile)

        return NOT_DONE_YET

    #
    pboxid = str(request.args['pboxid'])
    pboxid = strip_text(pboxid)
    filename = str(request.args['name'])
    filename = strip_text(filename)
    iv = str(request.args['iv'])
    iv = strip_text(iv)
    symkey = str(request.args['key'])
    symkey = strip_text(symkey)

    d = dbpool.runQuery(
        "INSERT INTO File (OwnerPBoxId, FileName, IV, SymKey) VALUES (?, ?, ?, ?);",
        (pboxid, filename, iv, symkey));
    d.addCallback(getFilePath)

    return NOT_DONE_YET


# Share related operations:
#


# Misc:
#

# strip_text(): helper function for stripping text from "[","]" and "'"
def strip_text(txt):
    txt = txt.strip("[")
    txt = txt.strip("]")
    txt = txt.strip("'")
    return txt

#TODO: add error handling on file io operations
# class FD2FileProducer:
class FD2FileProducer(object):
    interface.implements(iweb.IBodyProducer)

    def __init__(self, request, chunksize=200):
        self._file = request.content
        self._request = request
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

        data = None
        if not self._file.closed:
            data = self._file.read(self.chunksize)

            if data:
                self._consumer.write(data)
                self._scheduleSomeProducing()

        if not data :
            print "FINISHED0"
            if self._deferred is not None:
                print "FINISHED0"
                self._deferred.callback(None)
                self._deferred = None
                self._consumer.unregisterProducer()

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
        self.consumer.unregisterProducer()
        if self._delayedProduce is not None:
            self._delayedProduce.cancel()
        self._deferred = None
