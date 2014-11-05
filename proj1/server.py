from pprint import pprint

from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.internet import reactor, defer
from twisted.enterprise import adbapi
from twisted.web.server import NOT_DONE_YET

from datetime import datetime
import json

from  sfbx_srv_utils import *


# dbfilename = "safebox.sqlite"
# dbpool = adbapi.ConnectionPool("sqlite3", dbfilename, check_same_thread=False)

# class Session(Resource):
#     isLeaf = True

#     def render_POST(self, request):
#         pprint(request.__dict__)
#         #START SESSION
#         #END SESSION
#         newdata = request.content.getvalue()
#         print newdata
#         return "hello form"

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
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # list:
        if request.args['method'] == ['list']:
            print request.args['method']
            df = listPBoxes();
            df.addCallback(listPBoxes_cb, request)

        # get_mdata:
        elif request.args['method'] == ['get_mdata']:

            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'ccid' not provided."} }

            else:
                print request.args['ccid']
                df = getPBoxMData(request.args);
                df.addCallback(getPBoxMData_cb, request)

        # Unknown method:
        else:
            error = { 'status': {'error': "Invalid Request", 'reason': "Unknown method for this resource."} }

        if error != None:
            print request.args['method']
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        return NOT_DONE_YET


    # PUT Methods:
    #
    # register: To register (create) a new PBox.
    # 'method' = "register"
    # 'ccid' = <user's Portuguese Cityzen Card number>
    # 'name' = <user's real name>
    # 'pubkey' = <user's public key>
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        # register:
        if request.args['method'] == ['register']:
            print request.args['method']

            if 'ccid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'ccid' not specified."} }

            if ('name' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'name' not specified."} }

            if ('pubkey' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'pubkey' not specified."} }

            elif (error == None):
                df = registerPBox(request.args);
                df.addCallback(registerPBox_cb, request)

        else:
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        return NOT_DONE_YET

# The Files resource
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
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # list:
        if request.args['method'] == ['list']:
            if 'pboxid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'pboxid' not specified."} }

            elif (error == None):
                df = listFiles(request.args);
                df.addCallback(listFiles_cb, request)

            print request.args['method']

        # getfile:
        elif request.args['method'] == ['getfile']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'fileid' not specified."} }

            if ('pboxid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'pboxid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        return NOT_DONE_YET

    # POST Methods:
    #
    # updatefile: To update (reupload) a file.
    # 'method' = "updatefile"
    # 'fileid' = <the file id>
    def render_POST(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # updatefile:
        if request.args['method'] == ['updatefile']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'fileid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        newdata = request.content.getvalue()
        print newdata
        return NOT_DONE_YET

    # PUT Methods:
    #
    # putfile: To register (create) a new PBox.
    # 'method' = "putfile"
    # 'name' = <file name>
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        # putfile:
        if request.args['method'] == ['putfile']:
            if ('name' not in request.args.keys()):
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'name' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        newdata = request.content.getvalue()
        print newdata
        return NOT_DONE_YET

    # DELETE Methods:
    #
    # delete: To delete a file.
    # 'method' = "delete"
    # 'fileid' = <the file id>
    def render_DELETE(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # delete:
        if request.args['method'] == ['delete']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'fileid' not specified."} }

            print request.args['method']


        else:
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        return NOT_DONE_YET

# The Shares resource
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
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # getshared:
        if request.args['method'] == ['getshared']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'fileid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Unknown method for this resource."} }

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
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # sharefile:
        if request.args['method'] == ['sharefile']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'fileid' not specified."} }

            if ('ruserid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'ruserid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Unknown method for this resource."} }

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
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # updateshare:
        if request.args['method'] == ['updateshare']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'fileid' not specified."} }

            if ('ruserid' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'ruserid' not specified."} }

            if ('attrname' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'attrname' not specified."} }

            if ('newval' not in request.args.keys()) & (error == None):
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'newval' not specified."} }

            print request.args['method']

        # updatesfile:
        elif request.args['method'] == ['updatesfile']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'fileid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request", 'reason': "Unknown method for this resource."} }

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
    def render_DELETE(self, request):
        error = None;

        if 'method' not in request.args.keys():
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Argument 'method' not specified."} }
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # delete:
        if request.args['method'] == ['delete']:
            if 'fileid' not in request.args.keys():
                error = { 'status': {'error': "Invalid Request",
                         'reason': "Argument 'fileid' not specified."} }

            print request.args['method']

        else:
            error = { 'status': {'error': "Invalid Request",
                     'reason': "Unknown method for this resource."} }

        if error != None:
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        newdata = request.content.getvalue()
        print newdata
        return NOT_DONE_YET


if __name__ == "__main__":
    root = Resource()
#    root.putChild("session", Session())
    root.putChild("pboxes", PBoxes())
    root.putChild("files", Files())
    root.putChild("shares", Shares())
    factory = Site(root)
    reactor.listenTCP(8000, factory)
    reactor.run()
