from twisted.internet import stdio, reactor
from twisted.protocols import basic
from sfbx_client_utils import SafeBoxClient
import sys, os

class CommandReceiver(basic.LineReceiver):
    delimiter = "\n"
    control = 0

    def connectionMade(self):
        self.transport.write("Welcome to SafeBox command application.\n"
                             + "Type 'help' for help.\n"
                         )

    def lineReceived(self, line):
        if not line: return

        s = line.split()
        method = s[0].lower()

        # if state =

        if method == "list":
            return client.handleList(line)
        elif method == "get":
            return client.handleGet(line)
        elif method == "put":
            return client.handlePut(line)
        elif method == "update":
            return client.handleUpdate(line)
        elif method == "delete":
            return client.handleDelete(line)
        #for test purposes only
        elif method == "getkey":
            return client.handleGetKey()
        #for test purposes only
        elif method == "getticket":
            return client.handleGetTicket()
        #for test purposes only
        elif method == "getmdata":
            return client.handleGetMData()
        elif method == "help":
                 self.transport.write("\nThe availabe commands are:\nlist pboxes"
                                      + "\nlist files\nget file <fileId>\nupdate file <fileId>\n"
                                      + "delete file <fileId>\nshare file <fileId> <destinationPBoxId>\nquit\n")
        elif (method == "quit") or (method == "exit"):
            reactor.stop()
            self.transport.write("Bye Bye!")
        else:
            self.transport.write("Error: no such command.\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('Usage: %s <userccid> <password> <name(optional)>' % sys.argv[0])

    # dirname for the .pem files = user ccid
    if not os.path.exists(sys.argv[1]):
        sys.exit('ERROR: Directiry %s not found!' % sys.argv[1])

    if len(sys.argv) > 3:
        uname = sys.argv[3]
    else:
        uname = ""

    client =  SafeBoxClient()
    stdio.StandardIO(CommandReceiver())

    reactor.callLater(0, client.startClient, sys.argv[1], sys.argv[2], uname)
    reactor.run()
