from sfbx_access_control import ServerIdentity



if __name__ == "__main__":

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

    print dec_data == data

    
