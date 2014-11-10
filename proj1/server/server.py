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
    # getkey: To get the server's public key.
    # 'method' = "getkey"
    def render_GET(self, request):

        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # getticket:
        if request.args['method'] == ['getticket']:
            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
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
    #
    # get_mdata: To a pbox's metadata.
    # 'method' = "get_mdata"
    # 'usrccid' = <user's cc id number>
    def render_GET(self, request):

        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # list:
        if request.args['method'] == ['list']:
            print request.args['method']
            return handler.handleListPBoxes(request)

        # get_mdata:
        elif request.args['method'] == ['get_mdata']:

            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ccid' not provided."} }

            else:
                print request.args['ccid']
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

            if ('pubkey' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'pubkey' not specified."} }

            elif (error == None):
                return handler.handleRegisterPBox(request);

        error = { 'status': {'error': "Invalid Request",
                'message': "Unknown method for this resource."} }

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
    # 'pboxid' = <the pbox id>
    #
    # getfile: To download a file from user's pbox.
    # 'method' = "getfile"
    # 'fileid' = <the file id>
    # 'pboxid' = <the pbox id>
    def render_GET(self, request):
        print type(request.content)
        error = None;

        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # list:
        if request.args['method'] == ['list']:
            if 'pboxid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'pboxid' not specified."} }

            elif (error == None):
                return handler.handleListFiles(request)


        # getfile:
        elif request.args['method'] == ['getfile']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specifeid."} }

            if ('pboxid' not in request.args.keys()) & (error == None):
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
    # 'fileid' = <the file id>
    def render_POST(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        # putfile:
        if request.args['method'] == ['putfile']:
            if ('pboxid' not in request.args.keys()):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'pboxid' not specified."} }

            if ('name' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'name' not specified."} }

            if ('iv' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'iv' not specified."} }

            if ('key' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'key' not specified."} }

            print request.args['method']
            if error is None:
                return handler.handleUpdateFile(request)


        error = { 'status': {'error': "Invalid Request",
                'message': "Unknown method for this resource."} }
        pprint(request.__dict__)
        return json.dumps(error, sort_keys=True, encoding="utf-8")

    # PUT Methods:
    #
    # putfile: To upload a file.
    # 'method' = "putfile"
    # 'pboxid' = "<user's pbox id>"
    # 'name' = <file name>
    # 'iv' = <iv used to encrypt the file>
    # 'key' = <symmetric key used to encrypt the file>
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        # putfile:
        if request.args['method'] == ['putfile']:
            if ('pboxid' not in request.args.keys()):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'pboxid' not specified."} }

            if ('name' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'name' not specified."} }

            if ('iv' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'iv' not specified."} }

            if ('key' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                          'message': "Argument 'key' not specified."} }

            print request.args['method']
            if error is None:
                return handler.handlePutFile(request)


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
    # 'pboxid' = <the pbox id>
    # 'fileid' = <the file id>
    def render_DELETE(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # delete:
        if request.args['method'] == ['delete']:
            if 'pboxid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'pboxid' not specified."} }

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
    # 'method' = "getshared"
    # 'fileid' = <the file id>
    def render_GET(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # getshared:
        if request.args['method'] == ['getshared']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                     'message': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        return NOT_DONE_YET

    # POST Methods:
    #
    # sharefile: To share a file.
    # 'method' = "sharefile"
    # 'fileid' = <the file id>
    # 'ruserid' = <recipient's user id> TODO: define what this is!
    def render_POST(self, request):
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

            if ('ruserid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ruserid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                     'message': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        newdata = request.content.getvalue()
        print newdata
        return NOT_DONE_YET

    # PUT Methods:
    #
    # updateshare: To update a share (ex.: change write permissions).
    # 'method' = "updateshare"
    # 'fileid' = <the file id>
    # 'ruserid' = <recipient's user id> TODO: define what this is!
    # 'attrname' = <the share's attribute to change>
    # 'newval' = <the new value>
    #
    # updatesfile: To update (modify) a shared file.
    # 'method' = "updatesfile"
    # 'fileid' = <the file id>
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # updateshare:
        if request.args['method'] == ['updateshare']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specified."} }

            if ('ruserid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'ruserid' not specified."} }

            if ('attrname' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'attrname' not specified."} }

            if ('newval' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'newval' not specified."} }

            print request.args['method']

        # updatesfile:
        elif request.args['method'] == ['updatesfile']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                    'message': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        newdata = request.content.getvalue()
        print newdata
        return NOT_DONE_YET

    # DELETE Methods:
    #
    # delete: To delete (unshare) a shared file.
    # 'method' = "delete"
    # 'fileid' = <the file id>
    # 'pboxid' = <the user's pbox id>
    def render_DELETE(self, request):
        error = None;

        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'message': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # delete:
        if request.args['method'] == ['delete']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'message': "Argument 'fileid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                     'message': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        return NOT_DONE_YET


if __name__ == "__main__":

    handler = AccessCtrlHandler("rsakeys", "mypass")
    root = Resource()
    root.putChild("session", Session())
    root.putChild("pboxes", PBoxes())
    root.putChild("files", Files())
    root.putChild("shares", Shares())
    reactor.listenTCP(8000, Site(root))
    reactor.run()
