from pprint import pprint
#from twisted.application.internet import TCPServer
#from twisted.application.service import Application
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.internet import reactor
from twisted.enterprise import adbapi
#from twisted.web.server import NOT_DONE_YET

from datetime import datetime
import simplejson

# dbfilename = "test.sqlite"
# dbpool = adbapi.ConnectionPool("sqlite3", dbfilename, check_same_thread=False)

class Session(Resource):
    isLeaf = True

    def render_POST(self, request):
        pprint(request.__dict__)
        #START SESSION
        #END SESSION
        newdata = request.content.getvalue()
        print newdata
        return "hello form"

class PBoxes(Resource):
    isLeaf = True

    def render_GET(self, request):
        #GET THE LIST OF ALL PBOXES
        #GET METADATA FROM A SINGLE PBOX
        return ''

    def render_POST(self, request):
        pprint(request.__dict__)
        #REGISTER PBOX
        newdata = request.content.getvalue()
        print newdata
        return "hello form"

class Files(Resource):
    isLeaf = True

    def render_GET(self, request):
        #LIST ALL FILES ON USER'S PBOX
        #DOWNLOAD A FILE
        return ''

    def render_POST(self, request):
        pprint(request.__dict__)
        #UPLOAD A FILE
        newdata = request.content.getvalue()
        print newdata
        return "hello user"

    def render_PUT(self, request):
        pprint(request.__dict__)
        #UPDATE A FILE (AKA CHANGE THE FILE)
        newdata = request.content.getvalue()
        print newdata
        return "hello user"

    def render_DELETE(self, request):
        pprint(request.__dict__)
        #DELETE A FILE
        newdata = request.content.getvalue()
        print newdata
        return "hello user"


class Shares(Resource):
    isLeaf = True

    def render_GET(self, request):
        pprint(request.__dict__)
        #GET A SHARE (AKA DOWNLOAD THE SHARED FILE)
        return "hello user"

    def render_POST(self, request):
        pprint(request.__dict__)
        #SHARE A FILE (AKA CREATE A NEW SHARE)
        newdata = request.content.getvalue()
        print newdata
        return "hello user"

    def render_PUT(self, request):
        pprint(request.__dict__)
        #UPDATE A SHARE (I.E. CHANGE DE WRITE PERMISSIONS)
        #UPDATE A SHARED FILE (AKA CHANGE THE FILE)
        newdata = request.content.getvalue()
        print newdata
        return "hello user"

    def render_DELETE(self, request):
        pprint(request.__dict__)
        #DELETE A SHARE (AKA UNSHARE)
        newdata = request.content.getvalue()
        print newdata
        return "hello user"


if __name__ == "__main__":
    root = Resource()
    root.putChild("session", Session())
    root.putChild("pboxes", PBoxes())
    root.putChild("files", Files())
    root.putChild("shares", Shares())
    reactor.listenTCP(8000, Site(root))
    reactor.run()
