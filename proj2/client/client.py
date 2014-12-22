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

        if method == "list":
            if len(s) == 2:
                if s[1].lower() == "pboxes":
                    return client.handleListPboxes()
                elif s[1].lower() == "files":
                    return client.handleListFiles()
                elif s[1].lower() == "shares":
                    return client.handleListShares()
                else:
                    print "Error: invalid arguments!\n"
                    print "Correct usage: list <pboxes|files|shares>"
            else:
                print "Error: invalid arguments!\n"
                print "Correct usage: list <pboxes|files>"


        elif method == "get":
            if len(s) == 3:
                if s[1].lower() == "file":
                    return client.handleGetFile(s)
                if s[1].lower() == "pboxinfo":
                    return client.handleGetInfo(s)
                elif s[1].lower() == "fileinfo":
                    return client.handleGetInfo(s)
                elif s[1].lower() == "shareinfo":
                    return client.handleGetInfo(s)
                else:
                    print "Error: invalid arguments!\n"
                    print "Correct usage: get fileinfo <fileId> or get pboxinfo <PBox Owners CC Number>"
            elif len(s) == 4:
                if s[1].lower() == "file":
                    fileId = s[2]
                    return client.handleGetFile(s)

                if s[1].lower() == "shared":
                    fileId = s[2]
                    return client.handleGetShared(s)

                else:
                    print "Error: invalid arguments!\n"
                    print "Correct usage: get file|shared <fileId> <dest. filename on filesystem.>"
            else:
                print "Error: invalid arguments!\n"

        elif method == "put":
            if len(s) != 3:
                print "Error: invalid arguments!\n"
                return
            else:
                if s[1].lower() != "file":
                    print "Error: invalid arguments!\n"
                    print "Usage: put file <filepath>"
                    return
                elif not os.path.exists(s[2]):
                    print "Error: File " + s[2] + " does not exist.\n"
                    return

            return client.handlePutFile(line)

        elif method == "update":
            if len(s) == 5:
                if s[1] == "shareperm":
                    return client.handleUpdateSharePerm(s)
                print "Error: invalid arguments!\n"
                print "Usage: update shareperm <fileid> <rccid> <true>"
                return

            elif len(s) == 4:
                if not os.path.exists(s[3]):
                    print "Error: File " + s[3] + " does not exist.\n"
                    return
                if s[1] == "shared" or s[1] == "file":
                    return client.handleUpdate(s)

            print "Error: invalid arguments!\n"
            print "Usage: update <file|shared> <fileid> <local file path>"
            return

        elif method == "delete":
            return client.handleDelete(line)
        elif method == "share":
            return client.handleShare(line)
            #for test purposes only
        elif method == "getkey":
            return client.handleGetKey()
        elif method == "help":
            self.transport.write("\nThe availabe commands are:\nlist pboxes"
                                 + "\nlist files\nget file <fileId>\nupdate file <fileId>\n"
                                 + "\nget pboxinfo <ccid>\n"
                                 + "delete file <fileId>\nshare file <fileId> <destinationPBoxId>\nquit\n")
        elif (method == "quit") or (method == "exit"):
            reactor.stop()
            self.transport.write("Bye Bye!")
        else:
            self.transport.write("Error: no such command.\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('Usage: %s <userccid> <password> <name(optional)>' % sys.argv[0])

    # TODO: parse arguments propperly i.e.:Check password length

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
