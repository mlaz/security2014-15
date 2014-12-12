from sfbx_client_cryptography import ClientIdentity

if __name__ == "__main__":

        cid = ClientIdentity("111222333", "mypass", )
        f1 = open("recfile",'r')
        f2 = open("enc_recfile.exe",'w')

        creds = cid.encryptFileSym(f1,f2)
        f2 = open("enc_recfile.exe",'r')
        f3 = open("plain_recfile.exe",'w')
        print cid.decryptFileSym(f2,f3, creds[0], creds[1])
