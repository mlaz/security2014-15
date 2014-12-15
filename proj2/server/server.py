from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.internet import reactor, defer
from twisted.web.server import NOT_DONE_YET

#from datetime import datetime
from pprint import pprint

import json

from  sfbx_access_control import AccessCtrlHandler

# The Session Resource:
#
# Handles requests related to client id validation.
#
class Session(Resource):
    isLeaf = True

    # GET Methods:
    #
    # getticket: To get an access ticket.
    # 'method' = "getticket"
    # 'ccid' = <user's cc id number> #should we receive this encrypted
    #
    # getnonce: To get an authentication challange nonce.
    # 'method' = "getnonce"
    # 'ccid' = <user's cc id number> #should we receive this encrypted
    #
    # getkey: To get the server's public key.
    # 'method' = "getkey"
    def render_GET(self, request):

        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        # getnonce:
        if request.args['method'] == ['getnonce']:
            print request.args['method']
            return handler.handleGetNonce(request)

        # getticket:
        if request.args['method'] == ['getticket']:
            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invlid Request",
                         'message': "Argument 'ccid' not provided."} }
            else:
                print request.args['method']
                return handler.handleGetTicket(request)

        # getkey:
        elif request.args['method'] == ['getkey']:
            return handler.handleGetKey()

        # Unknown method:
        if error == None:
            error = { 'status': {'error': "Invalid Request",
                    'message': "Unknown method for this resource."} }

        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")

    # PUT Methods:
    #
    # register: To register (create) a new PBox.
    # 'method' = "start"
    # 'ccid' = <user's Portuguese Cityzen Card number>
    # 'name' = <user's real name>
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        # register:
        if request.args['method'] == ['register']:
            print request.args['method']

            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('name' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'name' not specified."} }

            # if ('pubkey' not in request.args.keys()) & (error == None):
            #     error = { 'status': {'error': "Invalid Request",
            #              'message': "Argument 'pubkey' not specified."} }

            elif (error == None):
                return handler.handleRegisterPBox(request);

        # startsession:
        if request.args['method'] == ['startsession']:
            print request.args['method']

            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('nonceid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'nonceid' not specified."} }

            elif (error == None):
                return handler.handleStartSession(request);


        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")

    # TODO: We will need to delete every entry reated to the given filenumber
    # on the Share table.
    # DELETE Methods:
    #
    # delete: To delete a file.
    # 'method' = "finish"
    # 'ccid' = <the ccid>
    # 'fileid' = <the file id>
    def render_DELETE(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # delete:
        if request.args['method'] == ['delete']:
            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('fileid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                        'message': "Argument 'fileid' not specified."} }

            print request.args['method']
            if error is None:
                return handler.handleDeleteFile(request)

        error = { 'status': {'error': "Invalid Request",
                    'message': "Unknown method for this resource."} }
        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")


# The PBoxes Resource:
#
# Handles requests related to PBoxes' ownership, browsing and discovery.
#
class PBoxes(Resource):
    isLeaf = True

    # GET Methods:
    #
    # list: To list all pboxes.
    # 'method' = "list"
    # 'ccid' = <user's cc id number>
    #
    # get_mdata: To a pbox's metadata.
    # 'method' = "get_mdata"
    # 'ccid' = <user's cc id number>
    # 'tgtccid' = <queried user's cc id number>
    def render_GET(self, request):

        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # list:
        if request.args['method'] == ['list']:


            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not provided."} }
            else:
                print request.args['method']
                return handler.handleListPBoxes(request)

        # get_mdata:
        elif request.args['method'] == ['get_mdata']:

            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not provided."} }

            if ('tgtccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'tgtccid' not specified."} }

            else:
                print request.args['tgtccid']
                return handler.handleGetPBoxMData(request)


        # Unknown method:
        if error == None:
            error = { 'status': {'error': "Invalid Request",
                    'message': "Unknown method for this resource."} }

        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")



    # PUT Methods:
    #
    # register: To register (create) a new PBox.
    # 'method' = "register"
    # 'ccid' = <user's Portuguese Cityzen Card number>
    # 'name' = <user's real name>
    # 'pubkey' = <user's public key> #TODO: receive this in body
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        # register:
        if request.args['method'] == ['register']:
            print request.args['method']

            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('name' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'name' not specified."} }

            # if ('pubkey' not in request.args.keys()) & (error == None):
            #     error = { 'status': {'error': "Invalid Request",
            #              'message': "Argument 'pubkey' not specified."} }

            elif (error == None):
                return handler.handleRegisterPBox(request);


        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")

# The Files Resource:
#
# Handles requests related to SafeBox's File ownership, browsing and discovery.
#
class Files(Resource):
    isLeaf = True

    # GET Methods:
    #
    # list: To list all files on user's pbox.
    # 'method' = "list"
    # 'ccid' = <the user cc id>
    #
    # getfilemdata: To download a file from user's pbox.
    # 'method' = "getfilemdata"
    # 'fileid' = <the file id>
    # 'ccid' = <the pbox id>
    #
    # getfile: To download a file from user's pbox.
    # 'method' = "getfile"
    # 'fileid' = <the file id>
    # 'ccid' = <the pbox id>
    def render_GET(self, request):
        print type(request.content)
        error = None;

        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # list:
        if request.args['method'] == ['list']:
            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            elif (error == None):
                return handler.handleListFiles(request)


        # getfilemdata:
        elif request.args['method'] == ['get_mdata']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specifeid."} }

            if ('ccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'pboxid' not specified."} }

            elif (error == None):
                return handler.handleGetFileMData(request)



        # getfile:
        elif request.args['method'] == ['getfile']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specifeid."} }

            if ('ccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'pboxid' not specified."} }

            elif (error == None):
                return handler.handleGetFile(request)


        elif (error == None):
            error = { 'status': {'error': "Invalid Request",
                        'message': "Unknown method for this resource."} }

        print request.args['method']
        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")


    # POST Methods:
    #
    # updatefile: To update (reupload) a file.
    # 'method' = "updatefile"
    # 'ccid' = <user's ccid>
    # 'fileid' = <the file id>
    # 'file' = <the file's new name>
    def render_POST(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        # updatefile:
        if request.args['method'] == ['updatefile']:
            if ('ccid' not in request.args.keys()):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('name' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'name' not specified."} }

            if ('fileid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'id' not specified."} }


            if error is None:
                return handler.handleUpdateFile(request)
        print request.args['method']

        error = { 'status': {'error': "Invalid Request",
                'message': "Unknown method for this resource."} }
        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")

    # PUT Methods:
    #
    # putfile: To upload a file.
    # 'method' = "putfile"
    # 'ccid' = <user's ccid>
    # 'name' = <file name>
    # 'iv' = <iv used to encrypt the file> # inside body
    # 'key' = <symmetric key used to encrypt the file> # inside body
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        # putfile:
        if request.args['method'] == ['putfile']:
            if ('ccid' not in request.args.keys()):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('name' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'name' not specified."} }

            print request.args['method']
            if error is None:
                return handler.handlePutFile(request)

        else:
            error = { 'status': {'error': "Invalid Request",
                    'message': "Unknown method for this resource."} }
        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")


    # TODO: We will need to delete every entry reated to the given filenumber
    # on the Share table.
    # DELETE Methods:
    #
    # delete: To delete a file.
    # 'method' = "delete"
    # 'ccid' = <the ccid>
    # 'fileid' = <the file id>
    def render_DELETE(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # delete:
        if request.args['method'] == ['delete']:
            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('fileid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                        'message': "Argument 'fileid' not specified."} }

            print request.args['method']
            if error is None:
                return handler.handleDeleteFile(request)

        error = { 'status': {'error': "Invalid Request",
                    'message': "Unknown method for this resource."} }
        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")



# The Shares Resource:
#
# Handles requests related to SafeBox's File sharing features.
#
class Shares(Resource):
    isLeaf = True

    # GET Methods:
    #
    # getshared: To download a shared file.
    # 'method' = "get_mdata"
    # 'ccid' = <user's ccid>
    # 'fileid' = <the file id>
    #
    # getshared: To download a shared file.
    # 'method' = "getshared"
    # 'ccid' = <user's ccid>
    # 'fileid' = <the file id>

    def render_GET(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # get_mdata:
        if request.args['method'] == ['get_mdata']:
            if ('ccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specified."} }

            print request.args['method']
            if error is None:
                return handler.handleGetShareMData(request)

        # getshared:
        if request.args['method'] == ['getshared']:
            if ('ccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specified."} }

            print request.args['method']
            if error is None:
                return handler.handleGetShared(request)

        # getshared:
        if request.args['method'] == ['list']:
            if ('ccid' not in request.args.keys()):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            print request.args['method']
            if error is None:
                return handler.handleListShares(request)


        else:
            error = { 'status': {'error': "Invalid Request",
                     'message': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

    # PUT Methods:
    #
    # sharefile: To share a file.
    # 'method' = "sharefile"
    # 'ccid' = <user's ccid> ADD CONDITIONS FOR THIS
    # 'fileid' = <the file id>
    # 'rccid' = <recipient's user id> TODO: define what this is!
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # sharefile:
        if request.args['method'] == ['sharefile']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specified."} }

            if ('ccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('rccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'rccid' not specified."} }

            if (request.args['rccid'] == request.args['ccid']) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Arguments 'rccid' and 'ccid' must be different."} }

            print request.args['method']
            if error == None:
                return handler.handleShareFile(request)
        else:
            error = { 'status': {'error': "Invalid Request",
                     'message': "Unknown method for this resource."} }

        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")

    # POST Methods:
    #
    # updateshare: To update a share (ex.: change write permissions).
    # 'method' = "updateshare"
    # 'ccid' = <user's ccid> ADD CONDITIONS FOR THIS
    # 'fileid' = <the file id>
    # 'rccid' = <recipient's user ccid> TODO: define what this is!
    # 'writeable' = <the new value, true or false>
    #
    # updatshareperm: read the source
    #
    # updateshared: To update (modify) a shared file.
    # 'ccid' = <user's ccid> ADD CONDITIONS FOR THIS
    # 'method' = "updatesfile"
    # 'fileid' = <the file id>
    def render_POST(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # updatshareperm:
        if request.args['method'] == ['updateshareperm']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specified."} }

            if ('ccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('rccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'rccid' not specified."} }

            if ('writeable' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'newval' not specified."} }

            if error == None:
                print request.args['method']
                return handler.handleUpdateSharePerm(request)

            print request.args['method']

        # updateshared:
        elif request.args['method'] == ['updateshared']:
            if ('ccid' not in request.args.keys()):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('name' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'name' not specified."} }

            if ('fileid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'id' not specified."} }
            print request.args['method']

            if error == None:
                return handler.handleUpdateShared(request)

        else:
            error = { 'status': {'error': "Invalid Request",
                    'message': "Unknown method for this resource."} }


        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")



    # DELETE Methods:
    #
    # delete: To delete (unshare) a shared file.
    # 'method' = "delete"
    # 'ccid' = <user's ccid> ADD CONDITIONS FOR THIS
    # 'fileid' = <the file id>
    # 'rccid' = <the recipient's ccid>
    def render_DELETE(self, request):
        error = None;

        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # delete:
        if request.args['method'] == ['delete']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specified."} }

            if ('ccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not specified."} }

            if ('rccid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'rccid' not specified."} }

            print request.args['method']
            if error == None:
                return handler.handleDeleteShare(request)

        else:
            error = { 'status': {'error': "Invalid Request",
                     'message': "Unknown method for this resource."} }


        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")




if __name__ == "__main__":

    handler = AccessCtrlHandler("rsakeys", "mypass")
    root = Resource()
    root.putChild("session", Session())
    root.putChild("pboxes", PBoxes())
    root.putChild("files", Files())
    root.putChild("shares", Shares())
    reactor.listenTCP(8000, Site(root))
    reactor.run()
