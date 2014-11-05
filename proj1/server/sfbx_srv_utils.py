from twisted.enterprise import adbapi
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

####### WIP ######
# returnFile(): Retrieves a file metadata.
def getFileInfo(args):
    fileid = str(args['fileid'])
    fileid = strip_text(fileid)

    return dbpool.runQuery(
        "SELECT * FROM File WHERE FileId = ?", (fileid,));

# retGetFile_cb(): Callback for registerPBox(), sends the file back to the client.
def retGetFile_cb (data, request):

    #TODO: Implement infrastructure for ownership checking (add field)
    if len(data) == 0:
        reply_dict = { 'status': {'error': "Unsuccessful db transaction", 'message': data} }

    else:
        row = data[0]
        file_name = row[0]
        sym_key = row[2]
        iv = row[2]

    #TODO: Here we shoud read the file
    # count = 0;
    # do:
    #     bytes_read = 0
    ##    read chunk_size bytes from file
    #     reply_dict = { 'status': "OK", 'chunk': bytes, 'count': count }
    #     request.write(json.dumps(reply_dict, encoding="utf-8"));
    #     count = count + 1
    # while ( (bytes_read !=0) && ((bytes_read % chunk_size) == 0) )
    # if bytes_read != 0
    #reply_dict = { 'status': {'error': "File size inconsistent"},
    #             'finish reason': 'EOF', 'nchunks': count }
    ##filesize must be multiple of chunksize else reply with error
    # reply_dict = { 'status': "OK", 'finish reason': 'EOF', 'nchunks': count }
    # request.write(json.dumps(reply_dict, encoding="utf-8"));
    # request.finish()

    request.write(json.dumps(reply_dict, encoding="utf-8"));
    request.finish()

##################


# Share related operations:
#



# strip_text(): helper function for stripping text from "[","]" and "'"
def strip_text(txt):
    txt = txt.strip("[")
    txt = txt.strip("]")
    txt = txt.strip("'")
    return txt
