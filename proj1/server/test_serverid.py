from sfbx_access_control import ServerIdentity, TicketManager



if __name__ == "__main__":

    print "Testing ServerIdentity: "
    sid = ServerIdentity("rsakeys", "mypass")
    print sid.priv_key
    print sid.pub_key
    print sid.priv_key.can_encrypt()
    print sid.pub_key.can_encrypt()

    signature = sid.signData("Hello!:)")
    print sid.verifySignature(signature, "Hello!:)")


    file = open("MyFile", 'r')
    data = file.read(100)

    enc_data = sid.encryptData(data)
    print enc_data

    dec_data = sid.decryptData(enc_data)
    print dec_data

    if dec_data == data:
        print "OK"

    print "Testing TicketManager: "

    tm = TicketManager(sid)
    t1 = tm.generateTicket(1, sid.pub_key)

    t1 = sid.decryptData(t1)
    sig1 = sid.signData(t1)
    sig1_enc = sid.encryptData(sig1)

    if tm.validateTicket(sig1_enc):
        print "OK"
