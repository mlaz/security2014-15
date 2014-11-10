from sfbx_access_control import ServerIdentity, TicketManager, AccessCtrlHandler
from Crypto import Random
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

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
    t1 = tm.generateTicket(1, sid.pub_key)
    print type(t1)
    print t1
    t1 = sid.decryptData(t1)

    hash = SHA256.new(t1)
    signer = PKCS1_v1_5.new(sid.priv_key)
    sig1 = signer.sign(hash)
    sig1_enc = sid.encryptData(sig1)

    if tm.validateTicket(sig1_enc, 1, sid.pub_key):
        print "OK"

    print "Testing AccessCtrlHandler: "

    handler = AccessCtrlHandler("rsakeys", "mypass")
    print handler.handleGetKey()
