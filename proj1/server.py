from pprint import pprint

from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.internet import reactor, defer
from twisted.enterprise import adbapi
from twisted.web.server import NOT_DONE_YET

from datetime import datetime
import json

dbfilename = "safebox.sqlite"
dbpool = adbapi.ConnectionPool("sqlite3", dbfilename, check_same_thread=False)

# class Session(Resource):
#     isLeaf = True

#     def render_POST(self, request):
#         pprint(request.__dict__)
#         #START SESSION
#         #END SESSION
#         newdata = request.content.getvalue()
#         print newdata
#         return "hello form"

# The PBoxes resource
class PBoxes(Resource):
    isLeaf = True

    # GET Methods:
    #
    # list: To list all pboxes.
    # 'method' = "list"
    #
    # get_mdata: To a pbox's metadata.
    # 'method' = "get_mdata"
    # 'fileid' = <the file id>
    def render_GET(self, request):

        def listPBoxes():
            return dbpool.runQuery("SELECT PBoxId, UserCCId, UserName FROM PBox")

        def listPBoxes_cb(data):
            print type(data)
            print type(data[0])
            pprint(data)
            data_dict = []

            for row in data:
                row_dict = {
                    'PBoxId' : row[0],
                    'UserCCId' : row[1],
                    'UserName' : row[2] }
                data_dict.append(row_dict)

            request.write(json.dumps(data_dict, encoding="utf-8"));
            request.finish()

        error = None;
        if 'method' not in request.args.keys():
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # list:
        if request.args['method'] == ['list']:
            print request.args['method']
            d = listPBoxes();
            d.addCallback(listPBoxes_cb)

        # get_mdata:
        elif request.args['method'] == ['get_mdata']:
            print request.args['method']

        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            print request.args['method']
            pprint(request.__dict__)
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        return NOT_DONE_YET


    # PUT Methods:
    #
    # register: To register (create) a new PBox.
    # 'method' = "register"
    # 'ccnumber' = <user's Portuguese Cityzen Card number>
    # 'name' = <user's reak name>
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        pprint(request.__dict__)

        # register:
        if request.args['method'] == ['register']:
            print request.args['method']

        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        newdata = request.content.getvalue()
        print newdata
        return "hello form"

# The Files resource
class Files(Resource):
    isLeaf = True

    # GET Methods:
    #
    # list: To list all files on user's pbox.
    # 'method' = "getshared"
    # 'fileid' = <the file id>
    #
    # getfile: To download a file from user's pbox.
    # 'method' = "getfile"
    # 'fileid' = <the file id>
    def render_GET(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        # list:
        if request.args['method'] == ['list']:
            print request.args['method']

        # getfile:
        elif request.args['method'] == ['getfile']:
            print request.args['method']

        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        return ''

    # POST Methods:
    #
    # updatefile: To update (reupload) a file.
    # 'method' = "updatefile"
    # 'fileid' = <the file id>
    def render_POST(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # updatefile:
        if request.args['method'] == ['updatefile']:
            print request.args['method']

        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        newdata = request.content.getvalue()
        print newdata
        return "hello user"

    # PUT Methods:
    #
    # putfile: To register (create) a new PBox.
    # 'method' = "putfile"
    # 'name' = <file name>
    def render_PUT(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # putfile:
        if request.args['method'] == ['putfile']:
            print request.args['method']

        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        newdata = request.content.getvalue()
        print newdata
        return "hello user"

    # DELETE Methods:
    #
    # delete: To delete a file.
    # 'method' = "delete"
    # 'fileid' = <the file id>
    def render_DELETE(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # delete:
        if request.args['method'] == ['delete']:
            print request.args['method']

        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            return json.dumps(error, sort_keys=True, encoding="utf-8")


        newdata = request.content.getvalue()
        print newdata
        return "hello user"

# The Shares resource
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
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # getshared:
        if request.args['method'] == ['getshared']:
            print request.args['method']

        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        return "hello user"

    # POST Methods:
    #
    # sharefile: To share a file.
    # 'method' = "sharefile"
    # 'fileid' = <the file id>
    # 'ruserid' = <recipient's user id> TODO: define what this is!
    def render_POST(self, request):
        error = None;
        if 'method' not in request.args.keys():
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # sharefile:
        if request.args['method'] == ['sharefile']:
            print request.args['method']

        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        newdata = request.content.getvalue()
        print newdata
        return "hello user"

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
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # updateshare:
        if request.args['method'] == ['updateshare']:
            print request.args['method']

        # updatesfile:
        elif request.args['method'] == ['updatesfile']:
            print request.args['method']

        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        newdata = request.content.getvalue()
        print newdata
        return "hello user"

    # DELETE Methods:
    #
    # delete: To delete (unshare) a shared file.
    # 'method' = "delete"
    # 'fileid' = <the file id>
    def render_DELETE(self, request):
        error = None;

        if 'method' not in request.args.keys():
            error = {"error": "Invalid Request", "reason": "Argument 'method' not specified."}
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        pprint(request.__dict__)

        # delete:
        if request.args['method'] == ['delete']:
            print request.args['method']
        else:
            error = {"error": "Invalid Request", "reason": "Unknown method for this resource."}

        if error != None:
            return json.dumps(error, sort_keys=True, encoding="utf-8")

        newdata = request.content.getvalue()
        print newdata
        return "hello user"


if __name__ == "__main__":
    root = Resource()
#    root.putChild("session", Session())
    root.putChild("pboxes", PBoxes())
    root.putChild("files", Files())
    root.putChild("shares", Shares())
    factory = Site(root)
    reactor.listenTCP(8000, factory)
    reactor.run()
