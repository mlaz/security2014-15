from twisted.internet import stdio, reactor
from twisted.protocols import basic
from sfbx_client_utils import SafeBoxClient

class Echo(basic.LineReceiver):
    delimiter = "\n"
    control = 0

    def connectionMade(self):
        self.transport.write("Welcome to SafeBox command application.\nType 'register <UserName> <ccNumber> <password>' or 'login <UserName> <password>' to start using the application\n")

    def lineReceived(self, line):
        if not line: return

        s = line.split()
        method = s[0].lower()
        
        if not self.control:
            if method == "register":
                self.control = 1
                return helper.handleRegister(line)
            elif method == "login":
                self.control = 1
                return helper.handleLogin(line)
            else:
                self.transport.write("Error: no such command\n")
        else:
            if method == "list":
                return helper.handleList(line)
            elif method == "get":
                return helper.handleGet(line)
            elif method == "put":
                return helper.handlePut(line)
            elif method == "update":
                return helper.handleUpdate(line)
            elif method == "delete":
                return helper.handleDelete(line)
            #for test purposes only
            elif method == "getkey":
                return helper.handleGetKey()
            #for test purposes only
            elif method == "getticket":
                return helper.handleGetTicket()
            #for test purposes only
            elif method == "getmdata":
                return helper.handleGetMData()
            elif method == "help":
                self.transport.write("\nThe availabe commands are:\nlist pboxes\nlist files\nget file <fileId>\nupdate file <fileId>\ndelete file <fileId>\nshare file <fileId> <destinationPBoxId>\nquit\n")
            elif method == "quit":
                reactor.stop()
                self.transport.write("Bye Bye!")
            else:
                self.transport.write("Error: no such command.\n")

if __name__ == "__main__":
    helper =  SafeBoxClient()
    stdio.StandardIO(Echo())
    reactor.run()
