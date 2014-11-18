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
import os

from sfbx_server_cryptography import ServerIdentity

IV_KEY_SIZE_B64 = 172

#
# SafeBox server storage utilities API:
# Provides facilities and utilities for preforming storage related operations
#

# Some utilities:
#

# strip_text(): helper function for stripping text from "[","]" and "'"
def strip_text(txt):
    txt = txt.strip("[")
    txt = txt.strip("]")
    txt = txt.strip("'")
    return txt

# class FD2FileProducer: This class is a IBodyProducer used to read chunked data from http requests
class FD2FileProducer(object):
    #TODO: add error handling on file io operations
    interface.implements(iweb.IBodyProducer)

    def __init__(self, request, chunksize=200):
        self._file = request.content
        if self._file is None:
            print "ERROR!!!"
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

# class SafeBoxStorage: This class provides methods for
# preforming operations on SafeBox's storage facilities (filesystem & database).
class SafeBoxStorage(object):
    from sfbx_access_control import ServerIdentity

    def __init__(self, server_id, dbfilename="safebox.sqlite"):
        self.dbpool = adbapi.ConnectionPool("sqlite3", dbfilename, check_same_thread=False)
        self.sid = server_id
# PBox related operations:
#

    # getClientData(): Retreives PBoxId and PubKey for internal usage.
    def getClientData(self, request):
        ccid_str = str(request.args['ccid'])
        ccid_str = strip_text(ccid_str)

        d = self.dbpool.runQuery(
            "SELECT PBoxId, PubKey FROM PBox WHERE UserCCId = ?", (ccid_str,))
        return d

    # listPBoxes(): Queries for all entries on PBox's basic meta-data attributes.
    def listPBoxes(self, request, pboxid, pubkey):
        # TODO: take
        # listPBoxes_cb(): Callback for listPBoxes(), processes retrieved data for reply.
        def listPBoxes_cb(data):
            data_dict = {}

            tsize = 0
            for row in data:
                row_dict = {
                   # 'PBoxId': row[0],
                    'UserCCId': row[1],
                    'UserName': row[2] }
                data_dict.update({tsize: row_dict})
                tsize = tsize + 1

            reply_dict = { 'status': "OK", 'size': tsize, 'list': data_dict }
            request.write(json.dumps(reply_dict, encoding="utf-8"));
            request.finish()

        d = self.dbpool.runQuery("SELECT PBoxId, UserCCId, UserName FROM PBox")
        d.addCallback(listPBoxes_cb)
        return NOT_DONE_YET


    # getPBoxMData(): Queries the data base for all
    # PBox's attributes for given ccid.
    def getPBoxMData(self, request, ignore, ignorekey):
        ccid_str = str(request.args['tgtccid'])
        ccid_str = strip_text(ccid_str)


        # getPBoxMData_cb(): Callback for getPBoxMData(), Processes retrieved data for reply.
        def getPBoxMData_cb (data):
            reply_dict = {}
            if len(data) == 0:
                reply_dict = { 'status': {'error': "Invalid Input", 'message': "User doesn't exist."} }

            else:
                for row in data:
                    row_dict = {
                        'PBoxId': row[0],
                        'UserCCId': row[1],
                        'UserName': row[3],
                        'PubKey': row[2],}
                    reply_dict.update(row_dict)

            reply_dict = {'status': "OK", 'data': reply_dict}
            request.write(json.dumps(reply_dict, encoding="utf-8"));
            request.finish()


        d = self.dbpool.runQuery(
            "SELECT * FROM PBox WHERE UserCCId = ?", (ccid_str,))
        d.addCallback(getPBoxMData_cb)
        return NOT_DONE_YET



    # registerPBox(): Inserts a new entry on PBox table.
    def registerPBox(self, request, pubkey):
        ccid = str(request.args['ccid'])
        ccid = strip_text(ccid)
        name = str(request.args['name'])
        name = strip_text(name)

        # registerPBox_cb(): Callback for registerPBox(),
        # produces reply according to registerPBox return value.
        def registerPBox_cb (data):
            if len(data) == 0:
                reply_dict = {'status': "OK"}

            else:
                reply_dict = { 'status': {'error': "Unsuccessful db transaction", 'message': "N/A"} }
                request.write(json.dumps(reply_dict, encoding="utf-8"));

            request.finish()


        d = self.dbpool.runQuery(
            "INSERT INTO PBox (UserCCId, UserName, PubKey) VALUES (?, ?, ?) ", (ccid, name, pubkey));
        d.addCallback(registerPBox_cb)
        return NOT_DONE_YET

    # File related operations:
    #
    # listFiles(): Retrieves FileName and FileId attributes for a given pboxid.
    def listFiles(self, request, pboxid, pubkey):
        # pboxid = str(request.args['pboxid'])
        # pboxid = strip_text(pboxid)

        # listFiles_cb(): Callback for listFiles(), produces the reply from the database query result.
        def listFiles_cb (data):
            data_dict = {}

            tsize = 0
            for row in data:
                row_dict = {
                    'FileName': row[0],
                    'FileId': row[1]}
                data_dict.update({tsize: row_dict})
                tsize = tsize + 1

            reply_dict = { 'status': "OK", 'size': tsize, 'list': data_dict }
            #pprint(reply_dict)
            request.write(json.dumps(reply_dict, encoding="utf-8"));
            request.finish()

        d = self.dbpool.runQuery(
            "SELECT FileName, FileId FROM File WHERE OwnerPBoxId = ?", (pboxid,));
        d.addCallback(listFiles_cb)
        return NOT_DONE_YET

    # getFileMData(): Queries the data base for  all
    # File's attributes for given file id and owner pboxid.
    def getFileMData(self, request, pboxid, pubkey):
        fileid = str(request.args['fileid'])
        fileid = strip_text(fileid)
        # getFileMData_cb(): Callback for getFileMData(), Processes retrieved data for response.
        def getFileMData_cb (data):
            reply_dict = {}
            if len(data) == 0:
                reply_dict = { 'status': {'error': "Invalid Input", 'message': "File unreachable."} }
            else:
             #   for row in data:
                iv_plain = self.sid.decryptData(data[0][3])
                iv = self.sid.encryptData(iv_plain, pubkey)
                row_dict = {
                    'OwnerPBoxId': data[0][1],
                    'FileName': data[0][2],
                    'IV': iv,
                    'SymKey': data[0][4],}
                reply_dict.update(row_dict)
                reply_dict = {'status': "OK", 'data': reply_dict}

            request.write(json.dumps(reply_dict, encoding="utf-8"));
            request.finish()

        d = self.dbpool.runQuery(
            "SELECT * FROM File WHERE FileId = ? AND OwnerPBoxId = ?", (fileid, pboxid))
        d.addCallback(getFileMData_cb)
        return NOT_DONE_YET

    # getFile(): Retrieves metadata for a given fileid,
    # then writes the file contents to the response body.
    def getFile(self, request, pboxid, pubkey):
        fileid = str(request.args['fileid'])
        fileid = strip_text(fileid)

        def finishTrnf_cb(ignored, file):
            file.close()
            request.finish()

        # getFile_cb(): Callback for getFile(), sends the file back to the client.
        def getFile_cb(data):
            if len(data) == 0:
                error = { 'status': {'error': "Invalid Request",
                                     'message': "File does not exist."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()
                return

            file_path = str(data[0][1]) + "/" + str(data[0][0])
            if not os.path.exists(file_path):
                error = { 'status': {'error': "Invalid Request",
                                     'message': "File does not exist."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()

            request.write(str(data[0][4]))
            iv_plain = self.sid.decryptData(data[0][3])
            print iv_plain
            iv = self.sid.encryptData(iv_plain, pubkey)
            request.write(iv)
            file = open(file_path ,"r")
            sender = FileSender()
            sender.CHUNK_SIZE = 200
            df = sender.beginFileTransfer(file, request)

            df.addErrback(err)
            df.addCallback(finishTrnf_cb, file)

        d = self.dbpool.runQuery(
            "SELECT * FROM File WHERE FileId = ? AND OwnerPBoxId = ?", (fileid,pboxid));
        d.addCallback(getFile_cb)
        return NOT_DONE_YET

    # putFile(): This method handles putfile method.
    # This is done in 3 steps:
    # 1 - Inserts entry on the Files table;
    # 2 - Queries for the new file's Id;
    # 3 - Write file to disk
    def putFile(self, request, pboxid, pubkey):
        #    pprint(request.__dict__)
        def finishRequest_cb(ignore,file):
            file.close()
            reply_dict = { 'status': "OK" }
            request.write(json.dumps(reply_dict, sort_keys=True, encoding="utf-8"))
            request.finish()

        # TODO: we shoud try a way of rollback
        #  if anything goes wrong at this point
        # This method should start writing the file to the disk.
        def writeFile_cb(data):
            # path = <OwnerPBoxId>/<FileId>
            if not os.path.exists(str(pboxid)):
                os.mkdir(str(pboxid))
            file = open(str(pboxid) + "/" + str(data[0][0]) ,"w")
            prod = FD2FileProducer(request)
            cons = FileConsumer(file)
            cons.registerProducer(prod, True)
            d = prod.startProducing(cons)
            d.addCallback(finishRequest_cb, file)

            return NOT_DONE_YET

        # This query should retreive the highest file number for a given pboxid
        def getFilePath_cb(data):
            d = self.dbpool.runQuery(
                "SELECT FileId " +
                "FROM File " +
                "WHERE OwnerPBoxId = ? " +
                "ORDER BY FileId DESC",
                (pboxid,))
            d.addCallback(writeFile_cb)

            return NOT_DONE_YET

        filename = str(request.args['name'])
        filename = strip_text(filename)
        symkey = request.content.read(IV_KEY_SIZE_B64)
        # print symkey
        iv = request.content.read(IV_KEY_SIZE_B64)
        # print iv
        d = self.dbpool.runQuery(
            "INSERT INTO File (OwnerPBoxId, FileName, IV, SymKey) VALUES (?, ?, ?, ?);",
            (pboxid, filename, iv, symkey));
        d.addCallback(getFilePath_cb)

        return NOT_DONE_YET

    # updateFile(): This method handles updatefile method.
    # This is done in 3 steps:
    # 1 - Updates entry on the Files table;
    # 2 - Write file to disk
    def updateFile(self, request, pboxid, pubkey):
        #    pprint(request.__dict__)
        def finishRequest_cb(ignore,file):
            file.close()
            reply_dict = { 'status': "OK" }
            request.write(json.dumps(reply_dict, sort_keys=True, encoding="utf-8"))
            request.finish()
            return


        # TODO: we shoud try a way of rollback
        #  if anything goes wrong at this point
        # This method should start writing the file to the disk.
        def writeFile_cb(data):
            if len(data) != 0:
                error = { 'status': {'error': "Invalid Request",
                        'message': "File unreachable."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()
                return

            # path = <OwnerPBoxId>/<FileId>
            # fileid = str(request.args['fileid'])
            # fileid = strip_text(fileid)
            file = open(str(pboxid) + "/" + fileid ,"w")
            prod = FD2FileProducer(request)
            cons = FileConsumer(file)
            cons.registerProducer(prod, True)
            d = prod.startProducing(cons)
            d.addCallback(finishRequest_cb, file)

            return NOT_DONE_YET

        filename = str(request.args['name'])
        filename = strip_text(filename)
        fileid = str(request.args['fileid'])
        fileid = strip_text(fileid)
        iv = request.content.read(IV_KEY_SIZE_B64)

        if os.path.exists(str(pboxid) + "/" + fileid) == True:
            df = self.dbpool.runQuery(
                "UPDATE File " +
                "SET IV = ?, FileName = ? " +
                "WHERE FileId = ? AND OwnerPBoxId = ? ",
                (iv, filename, fileid, pboxid))
            df.addCallback(writeFile_cb)
            return NOT_DONE_YET
        else:
            error = { 'status': {'error': "Invalid Request",
                        'message': "File does not exist."} }
            request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
            request.finish()

    #TODO add some error handling to file I/O operations
    #deleteFile: Checks if a given file exists on fs and db then deletes it.
    def deleteFile(self, request, pboxid, pubkey):
        fileid = str(request.args['fileid'])
        fileid = strip_text(fileid)
        file_path = str(pboxid) + "/" + fileid

        # 3 - Deleting the file.
        def deleteAndFinish_cb(ignored):
            os.remove(file_path)
            request.finish()

        # 2 - Deleting table entry for referenced file if the file exists.
        def checkAndDelete_cb(data):
            if len(data) == 0:
                error = { 'status': {'error': "Invalid Request",
                        'message': "File does not exist."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()

            else:
                df = self.dbpool.runQuery(
                    "DELETE " +
                    "FROM File " +
                    "WHERE FileId = ? AND OwnerPBoxId = ? ",
                    (fileid, pboxid))
                df.addCallback(deleteAndFinish_cb)

        # 1 - Checking if the file exists.
        if os.path.exists(file_path) == True:
            df = self.dbpool.runQuery(
                "SELECT FileId, OwnerPBoxId " +
                "FROM File " +
                "WHERE FileId = ? AND OwnerPBoxId = ? " +
                "ORDER BY FileId DESC",
                (fileid, pboxid))
            df.addCallback(checkAndDelete_cb)
            return NOT_DONE_YET

        # the file does not exist on fs.
        error = { 'status': {'error': "Invalid Request",
                        'message': "File does not exist."} }
        return json.dumps(error, sort_keys=True, encoding="utf-8")



# Share related operations:
#
    def shareFile(self, request, pboxid, pubkey):
        fileid = str(request.args['fileid'])
        fileid = strip_text(fileid)
        rccid = str(request.args['rccid'])
        rccid = strip_text(rccid)
        file_path = str(pboxid) + "/" + fileid

        # 3 - Writing feedback
        def writereply_cb(ignored):
            reply_dict = { 'status': "OK" }
            request.write(json.dumps(reply_dict, sort_keys=True, encoding="utf-8"))
            request.finish()
            return

        # 2 - Deleting table entry for referenced file if the file exists.
        def checkAndShare_cb(data):
            if len(data) == 0:
                error = { 'status': {'error': "Invalid Request",
                        'message': "File does not exist."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()

            else:
                symkey = request.content.read(IV_KEY_SIZE_B64)
                df = self.dbpool.runQuery(
                    "INSERT " +
                    "Into Share (FileId, ForeignPBoxId, Symkey, Writeable) " +
                    "VALUES ( ?, (SELECT PBoxID FROM PBox WHERE UserCCId = ?), ?, 1)",
                    (fileid, rccid, symkey))
                df.addCallback(writereply_cb)

        # 1 - Checking if the file exists.
        if os.path.exists(file_path) == True:
            df = self.dbpool.runQuery(
                "SELECT FileId, OwnerPBoxId " +
                "FROM File " +
                "WHERE FileId = ? AND OwnerPBoxId = ? " +
                "ORDER BY FileId DESC",
                (fileid, pboxid))
            df.addCallback(checkAndShare_cb)
            return NOT_DONE_YET

        # the file does not exist on fs.
        error = { 'status': {'error': "Invalid Request",
                        'message': "File does not exist."} }
        return json.dumps(error, sort_keys=True, encoding="utf-8")

    # getshared(): Retrieves metadata for a given shared fileid,
    # then writes the file contents to the response body along with IV and Key.
    def getShared(self, request, pboxid, pubkey):
        fileid = str(request.args['fileid'])
        fileid = strip_text(fileid)

        def finishTrnf_cb(ignored, file):
            file.close()
            request.finish()

        # getshared_cb(): Callback for getshared(), sends the file back to the client.
        def getshared_cb(data):
            if len(data) == 0:
                error = { 'status': {'error': "Invalid Request",
                                     'message': "File does not exist."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()
                return

            file_path = str(data[0][0]) + "/" + fileid
            if not os.path.exists(file_path):
                error = { 'status': {'error': "Invalid Request",
                                     'message': "File does not exist."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()

            request.write(str(data[0][1])) # writing key
            iv_plain = self.sid.decryptData(data[0][2]) # writing IV
            print iv_plain
            iv = self.sid.encryptData(iv_plain, pubkey)
            request.write(iv)
            file = open(file_path ,"r")
            sender = FileSender()
            sender.CHUNK_SIZE = 200
            df = sender.beginFileTransfer(file, request)

            df.addErrback(err)
            df.addCallback(finishTrnf_cb, file)

        d = self.dbpool.runQuery(
             "SELECT File.OwnerPBoxId, Share.SymKey, File.IV  " +
            "FROM Share JOIN File ON File.FileId = Share.FileId " +
            "AND Share.FileID = ? AND Share.ForeignPBoxId = ?", (fileid,pboxid));
        d.addCallback(getshared_cb)
        return NOT_DONE_YET

    # getShareMData(): Queries the data base for  all
    # File's attributes for given file id and owner pboxid.
    def getShareMData(self, request, pboxid, pubkey):
        fileid = str(request.args['fileid'])
        fileid = strip_text(fileid)
        # getShareMData_cb(): Callback for getShareMData(), Processes retrieved data for response.
        def getShareMData_cb (data):
            reply_dict = {}
            if len(data) == 0:
                reply_dict = { 'status': {'error': "Invalid Input", 'message': "File unreachable."} }
            else:
             #   for row in data:
                iv_plain = self.sid.decryptData(data[0][2])
                iv = self.sid.encryptData(iv_plain, pubkey)
                row_dict = {
                    'FileName': data[0][0],
                    'SymKey': data[0][1],
                    'IV': iv,
                    'Writeable': data[0][3],}
                reply_dict.update(row_dict)
                reply_dict = {'status': "OK", 'data': reply_dict}

            request.write(json.dumps(reply_dict, encoding="utf-8"));
            request.finish()

        d = self.dbpool.runQuery(
            "SELECT File.FileName, Share.SymKey, File.IV, Share.Writeable " +
            "FROM Share JOIN File ON File.FileId = Share.FileId " +
            "AND Share.FileID = ? AND Share.ForeignPBoxId = ?", (fileid,pboxid));
        d.addCallback(getShareMData_cb)
        return NOT_DONE_YET

    # updateShare(): This method handles updateshare method.
    # This is done in 3 steps:
    # 1 - Checks if user has write permission;
    # 2 - Updates entry on the Files table;
    # 3 - Write shared file to disk
    def updateShared(self, request, pboxid, pubkey):
        #    pprint(request.__dict__)
        def finishRequest_cb(ignore,file):
            file.close()
            reply_dict = { 'status': "OK" }
            request.write(json.dumps(reply_dict, sort_keys=True, encoding="utf-8"))
            request.finish()
            return

        # TODO: we shoud try a way of rollback
        #  if anything goes wrong at this point
        # This method should start writing the file to the disk.
        def writeFile_cb(data, ownerid):
            if len(data) != 0:
                error = { 'status': {'error': "Invalid Request",
                        'message': "File unreachable."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()
                return

            # path = <OwnerPBoxId>/<FileId>
            file = open(str(ownerid) + "/" + fileid ,"w")
            prod = FD2FileProducer(request)
            cons = FileConsumer(file)
            cons.registerProducer(prod, True)
            d = prod.startProducing(cons)
            d.addCallback(finishRequest_cb, file)

            return NOT_DONE_YET

        def updateFileTable_cb(data):
            if len(data) == 0:
                print "HERE"
                error = { 'status': {'error': "Invalid Request",
                        'message': "File unreachable."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()
                return

            if data[0][1] == 0: #checking if the user has permission for this
                error = { 'status': {'error': "Invalid Request",
                        'message': "Permission denied."} }
                request.write(json.dumps(error, sort_keys=True, encoding="utf-8"))
                request.finish()
                return

            filename = str(request.args['name'])
            filename = strip_text(filename)
            fileid = str(request.args['fileid'])
            fileid = strip_text(fileid)
            iv = request.content.read(IV_KEY_SIZE_B64)


            df = self.dbpool.runQuery(
                "UPDATE File " +
                "SET IV = ?, FileName = ? " +
                "WHERE FileId = ? AND OwnerPBoxId = ? ",
                (iv, filename, fileid, data[0][0]))
            df.addCallback(writeFile_cb, data[0][0])
            return NOT_DONE_YET

        fileid = str(request.args['fileid'])
        fileid = strip_text(fileid)

        df = self.dbpool.runQuery(
            "SELECT File.OwnerPBoxId, Share.Writeable " +
            "FROM Share JOIN File ON File.FileId = Share.FileId " +
            "AND Share.FileID = ? AND Share.ForeignPBoxId = ?", (fileid,pboxid));
        df.addCallback(updateFileTable_cb)
        return NOT_DONE_YET

    # updateSharePerm(): Queries the data base for  all
    # File's attributes for given file id and owner pboxid.
    def updateSharePerm(self, request, pboxid, pubkey):
        return
        # # updateSharePerm_cb(): Callback for updateSharePerm(), Processes retrieved data for response.
        # def updateSharePerm_cb (data):
        #     reply_dict = {}
        #     if len(data) == 0:
        #         reply_dict = { 'status': {'error': "Invalid Input", 'message': "File unreachable."} }
        #     else:
        #         df = self.dbpool.runQuery(
        #         "UPDATE Share " +
        #         "SET IV = ?, FileName = ? " +
        #         "WHERE FileId = ? AND PBoxId = ? ",
        #         (iv, filename, fileid, pboxid))
        #     request.write(json.dumps(reply_dict, encoding="utf-8"));
        #     request.finish()

        # fileid = str(request.args['fileid'])
        # fileid = strip_text(fileid)
        # rccid = str(request.args['rccid'])
        # rccid = strip_text(rccid)
        # writeable = str(request.args['writeable'])
        # writeable = strip_text(writable)

        # if writeable == "true":
        #     writeable = 1
        # else:
        #     writeable = 0

        # d = self.dbpool.runQuery(
        #     "SELECT Share.ForeignPboxId, Share.Writeable " +
        #     "FROM Share JOIN File ON File.FileId = Share.FileId " +
        #     "AND Share.FileID = ? AND Share.ForeignPBoxId = ? AND File.OwnerPBoxId"w, (fileid,pboxid));
        # d.addCallback(updateSharePerm_cb)
        # return NOT_DONE_YET

    # #TODO add some error handling to file I/O operations
    # #deleteFile: Checks if a given file exists on fs and db then deletes it.
    # def deleteShare(self, request):
    #     pboxid = str(request.args['pboxid'])
    #     pboxid = strip_text(pboxid)
    #     fileid = str(request.args['fileid'])
    #     fileid = strip_text(fileid)
    #     file_path = pboxid + "/" + fileid

    #     # 3 - Deleting the file.
    #     def deleteAndFinish_cb(ignored):
    #         os.remove(file_path)
    #         request.finish()

    #     # 2 - Deleting table entry for referenced file if the file exists.
    #     def checkAndDelete_cb(data):
    #         if len(data) == 0:
    #             #write some error msg
    #             request.finish()

    #         else:
    #             df = self.dbpool.runQuery(
    #                 "DELETE " +
    #                 "FROM File " +
    #                 "WHERE FileId = ? AND OwnerPBoxId = ? ",
    #                 (fileid, pboxid))
    #             df.addCallback(deleteAndFinish_cb)

    #     # 1 - Checking if the file exists.
    #     if os.path.exists(file_path) == True:
    #         df = self.dbpool.runQuery(
    #             "SELECT FileId, OwnerPBoxId " +
    #             "FROM File " +
    #             "WHERE FileId = ? AND OwnerPBoxId = ? " +
    #             "ORDER BY FileId DESC",
    #             (fileid, pboxid))
    #         df.addCallback(checkAndDelete_cb)
    #         return NOT_DONE_YET

    #     # the file does not exist on fs.
    #     #write some error msg "
    #     request.finish() #instead of this return error
