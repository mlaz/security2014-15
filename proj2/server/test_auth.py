from sfbx_access_control import  AccessCtrlHandler
from sfbx_server_cryptography import ServerIdentity
from sfbx_authentication import TicketManager, SessionManager, AuthManager

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

    enc_data = sid.encryptData(data, None)
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
    dec_t1 = sid.decryptData(str(t1))
    hash = SHA256.new(dec_t1)
    signer = PKCS1_v1_5.new(sid.priv_key)
    sig1 = signer.sign(hash)
    sig1_enc = sid.encryptData(sig1)
#/client

    print tm.validateTicket(str(sig1_enc), 1, sid.pub_key.exportKey())

    print "Testing AuthManager: "
    pboxid = 26
    auth = AuthManager(sid)
    (enc_nonce, nonceid) = auth.generateNonce(sid.pub_key.exportKey())

#client
    nonce = sid.decryptData(enc_nonce, None)
    print nonce
    hash = SHA256.new(nonce)
    signer = PKCS1_v1_5.new(sid.priv_key)
    sig2 = signer.sign(hash)
    print sig2
    sig2_enc = sid.encryptData(sig2)
#/client

    print auth.validateNonce(sig2_enc, nonceid, sid.pub_key.exportKey())

    print "Testing SessionManager: "
    pboxid = 26
    sess = SessionManager(sid)
    auth = sess.authm

    (enc_nonce, nonceid) = auth.generateNonce(sid.pub_key.exportKey())

#client
    nonce = sid.decryptData(enc_nonce, None)
    print nonce
    hash = SHA256.new(nonce)
    signer = PKCS1_v1_5.new(sid.priv_key)
    sig2 = signer.sign(hash)
    print sig2
    sig2_enc = sid.encryptData(sig2)
#/client

    if sess.startSession(sig2_enc, nonceid, sid.pub_key.exportKey(), pboxid):
        print "SessionStarted"
    else: print "Error: couldn't start session."


    print sess.hasSession(pboxid)

    sess.refreshSession(pboxid)
    print sess.hasSession(pboxid)

    sess.finishSession(pboxid)
    print sess.hasSession(pboxid) #  should return false
    # print "Testing AccessCtrlHandler: "

    # handler = AccessCtrlHandler("rsakeys", "mypass")
    # print handler.handleGetKey()
