from sfbx_access_control import ServerIdentity, TicketManager, AccessCtrlHandler
from Crypto import Random
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from base64 import b64encode, b64decode

if __name__ == "__main__":

    print "Testing ServerIdentity: "

    sid = ServerIdentity("rsakeys", "mypass")
    print sid.priv_key
    print sid.pub_key
    print sid.priv_key.can_encrypt()
    print sid.pub_key.can_encrypt()

    signature = sid.signData("Hello!:)")
    print sid.verifySignature(signature, "Hello!:)")

    data = str(Random.get_random_bytes(64))

    enc_data = sid.encryptData(data, sid.pub_key)
    print enc_data

    print type(enc_data)

    dec_data = sid.decryptData(enc_data)
    print dec_data

    if dec_data == data:
        print "OK"



    print "Testing TicketManager: "

    tm = TicketManager(sid)
    t1 = tm.generateTicket(1, sid.pub_key.exportKey('PEM'))
    print type(t1)
    print t1
#    print len(str(b64encode(t1[0])))
#    t1 = str(b64encode(t1[0]))

#client
    dec_t1 = sid.decryptData(b64decode(str(t1)))
    hash = SHA256.new(dec_t1)
    signer = PKCS1_v1_5.new(sid.priv_key)
    sig1 = signer.sign(hash)
    sig1_enc = sid.encryptData(sig1)
    sig1_enc = b64encode(sig1_enc[0])

#/client
#server
    if tm.validateTicket(str(sig1_enc), 1, sid.pub_key):
        print "OK"


    print "Testing AccessCtrlHandler: "

    handler = AccessCtrlHandler("rsakeys", "mypass")
    print handler.handleGetKey()
