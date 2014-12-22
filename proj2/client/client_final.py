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
            return client.handlePutFile(line)
        elif method == "update":
            return client.handleUpdate(line)
        elif method == "delete":
            return client.handleDelete(line)
        elif method == "share":
            return client.handleShare(line)
        #for test purposes only
        elif method == "getkey":
            return client.handleGetKey()
        #for test purposes only
        elif method == "getticket":
            return client.handleGetTicket()
        elif method == "help":
                 self.transport.write("\nThe availabe commands are:\nlist pboxes | list files | list shares"
                                      + "\nget MData <target's CC Id> | get file MData <file Id> | get share MData <file Id>" +
                                      + "\nget file <file Id> | get shared <file Id>"
                                      + "\nput file <file name>\n"
                                      + "\nupdate file <file Id> <file name> | update shared <file Id> <file name>"
                                      + "\ndelete file <file Id> | delete shared <file Id> <target's CC Id>"
                                      + "\nshare file <file Id> <target's CC Id>"
                                      + "\nquit")
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
