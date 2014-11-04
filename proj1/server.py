from twisted.internet import reactor
from twisted.web import server, resource
from twisted.web.static import File

user1={"name":"john", "surname":"smith", "age":23, "email":"john@foo.bar"}
user2={"name":"davide", "surname":"carboni", "age":35, "email":"davide@foo.bar"}
user3={"name":"stefano", "surname":"sanna", "age":32, "email":"stefano@foo.bar"}

users=[user1,user2,user3]

class Root(resource.Resource):
    isLeaf=False

    def render_GET(self, request):
        return "Arkanoid?"





class ListUsers(resource.Resource):
    isLeaf=True

def render_GET(self, request):
    userList=[us['name'] for us in users]
    return str(userList)




class User(resource.Resource):
    isLeaf=True
    def render_GET(self, request):
        name=request.args['name'][0]
        record=filter(lambda(x): name==x['name'], users)[0]
        return str(record)



def render_POST(self,request):
    record=eval(request.content.read())
    #WARNING. USING EVAL ON USER TRANSMITTED DATA
    #IS A SEVERE SECURITY FLAW.
    #USE A PARSER LIKE SIMPLEJSON INSTEAD

    users.append(record)g(x): name==x['name'], users)[0]
    users.remove(record)
    return "OK"


if __name__ == "__main__":
    root=Root()
    root.putChild("user",User())
    root.putChild("listUsers",ListUsers())
    root.putChild("d",File("."))
    site = server.Site(root)
    reactor.listenTCP(8000, site)
    reactor.run()

