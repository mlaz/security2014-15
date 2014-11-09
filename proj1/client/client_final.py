from twisted.internet import stdio, reactor
from twisted.protocols import basic
from sfbx_client_utils import SafeBoxClient

class Echo(basic.LineReceiver):
    delimiter = "\n"

    def connectionMade(self):
        self.transport.write("Welcome to SafeBox command application.\nType help to see a list of commands.\n")

    def lineReceived(self, line):
        if not line: return

        s = line.split()
        method = s[0].lower()
        
        if method == "list":
            print "in list"
#           helper = SafeBoxClient()
            return helper.handleList(line)
        elif method == "get":
            print "in get"
            return helper.handleGet(line)
        elif method == "put":
            print "in put"
            return helper.handlePut(line)
        elif method == "update":
            print "in update"
            return helper.handleUpdate(line)
        elif method == "delete":
            print "in delete"
            return helper.handleDelete(line)
        elif method == "help":
            self.sendLine("\nThe availabe commands are:\nlist pboxes\nlist files\nget file <fileId>\nupdate file <fileId>\ndelete file <fileId>\nquit")
        elif method == "quit":
            reactor.stop()
            self.sendLine("Bye Bye!")
        else:
            self.sendLine("Error: no such command.")

if __name__ == "__main__":
    helper =  SafeBoxClient()
    stdio.StandardIO(Echo())
    reactor.run()
