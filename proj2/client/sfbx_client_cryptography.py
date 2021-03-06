from twisted.internet.protocol import Protocol
from twisted.internet import defer, reactor
from twisted.web.server import NOT_DONE_YET

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256, HMAC
from Crypto.Util import number
from Crypto import Random

from base64 import b64encode, b64decode
from pprint import pprint
import json

from sfbx_decode_utils import *
import sfbx_cc_utils as cc

BSIZE = AES.block_size
CHUNK_SIZE = 160
IV_KEY_SIZE_B64 = 172

#
# SafeBox client crypography utilities API:
# Provides facilities and utilities for preforming cryptographic operations
# on files and identification processes.
#

# class ClientIdentity:
# This class provides a facility for managing the application's cryptographic identity
# and preforming cryptographic operations on given data.
class ClientIdentity(object):

    def __init__(self, dir_name, password, server_key=None):
        file = open(dir_name + "/private.pem", 'r')
        self.priv_key = RSA.importKey(file.read(), password)
        file.close()

        file = open(dir_name + "/public.pem", 'r')
        self.pub_key = RSA.importKey(file.read(), password)
        file.close()

        self.password = password

        if server_key is not None: ## it only is None for testing purposes
            self.server_key = RSA.importKey(server_key)

        self.signer = PKCS1_v1_5.new(self.priv_key)
        self.verifier = PKCS1_v1_5.new(self.pub_key)

        self.rnd = Random.new()

    def encryptData(self, data, key=None):
        if key is None:
            key = self.server_key
        return b64encode(key.encrypt(data, self.rnd.read)[0]) #TODO: Be sure about this!

    def decryptData(self, data, key=None):
        if key is None:
            key = self.priv_key
        data = b64decode(data)
        return key.decrypt(data)

    def signData(self, data):
        hash = SHA256.new(data)
        return self.signer.sign(hash)

    def verifySignature(self, signature, data, key=None):
        if key is None:
            key = self.pub_key
        hash = SHA256.new(data)
        return self.verifier.verify(hash, signature)

    # Symmetric cypher encryption

    #encryptFileSym
    def encryptFileSym(self, src_file, dst_file, key=None, iv=None):
        if key is None:
            key = self.rnd.read(BSIZE)
        if iv is None:
            iv = self.rnd.read(BSIZE)

        cipher = AES.new(key, AES.MODE_OFB, iv)

        data = src_file.read(CHUNK_SIZE)
        cnt=0
        while(data):
            if len(data) % BSIZE is not 0:
                data = data + (BSIZE - len(data) % BSIZE) * chr(BSIZE - len(data) % BSIZE)

            #print str(data)
            enc_data = cipher.encrypt(data)

            dst_file.write(enc_data)
            data = src_file.read(CHUNK_SIZE)
            cnt = cnt + len(enc_data)
            #print cnt
        src_file.close()
        dst_file.close()
        return (key, iv)

    #decryptFileSym
    def decryptFileSym(self, src_file, dst_file, key, iv):
        cipher = AES.new(key, AES.MODE_OFB, iv)
        enc_data = src_file.read(CHUNK_SIZE)
        cnt=0
        while(enc_data):
            cnt = cnt + len(enc_data)
            #print cnt
            data = cipher.decrypt(enc_data)
            #print data
            enc_data = src_file.read(CHUNK_SIZE)
            if len(enc_data) == 0:
                pad = ord(data[-1])
                data = data[:-pad]
            dst_file.write(data)
        src_file.close()
        dst_file.close()
        return (key, iv)

    # Argument integrity utilities
    # Concatenates and hashes a string list with given salt
    def genHashArgs(self, args, salt):
        #print "salt", salt
        args = sorted(args)
        args_str = "".join(args)
        hash = HMAC.new(salt, digestmod=SHA256)
        hash.update(str(args_str))
        return b64encode(hash.hexdigest())

# Some utilities:
#

# getTicket Protocol:
class getTicket(Protocol):
    def __init__(self, finished, ci):
        self.finished = finished
        self.ci = ci #the clientid
        self.total_response = ""

    def dataReceived(self, bytes):
        self.total_response += bytes

    def connectionLost(self, reason):
        finalTicket = self.formatTicket(self.total_response)
        self.finished.callback(finalTicket)

    def formatTicket(self, response):

        response = json.loads(response)

        if response["status"] != "OK" :
            print(response["status"]["error"])
            return None
        else:
            s = response["ticket"]
            #print "Encrypted Ticket: ", s
            cryTicket = self.process_ticket(str(s))
            #print "Decrypted Ticket: ", cryTicket
            return cryTicket

    def process_ticket(self, ticket):
        # print "server's ticket: ", ticket
        dci = number.long_to_bytes(number.bytes_to_long(self.ci.decryptData(ticket)) + long("1", base=10))
        sci = self.ci.signData(str(dci))
        enc = self.ci.encryptData(sci)
        #enc = b64encode(eci[0])
        # print "signed and encoded ticket: " + enc
        return enc

# getNonce Protocol:
class getNonce(Protocol):
    def __init__(self, finished, ci, pin):
        self.finished = finished
        self.ci = ci #the clientid
        self.total_response = ""
        self.pin = pin #cc pin

    def dataReceived(self, bytes):
        self.total_response += bytes

    def connectionLost(self, reason):
        (finalNonce, nonceid) = self.formatNonce(self.total_response)
        self.finished.callback((finalNonce, nonceid))

    def formatNonce(self, response):

        response = json.loads(response)

        if response["status"] != "OK" :
            print(response["status"]["error"])
            return None
        else:
            s = response["nonce"]
            #print "Encrypted Nonce: ", s
            cryNonce = self.process_nonce(str(s))
            #print "Decrypted Nonce: ", cryNonce
            return (cryNonce, response["nonceid"])

    def process_nonce(self, nonce):
        dci = self.ci.decryptData(nonce)
        #print "client's nonce: ", dci
        #sci = self.ci.signData(dci)
        #print "signed nonce: ", sci
        if self.pin is None:
            print "ERROR! Check the pin or the card!"
            reactor.stop()
        sci = cc.sign(dci, cc.KEY_LABEL, self.pin)
        #print "nonce signed w/ CC: ", sci
        enc = self.ci.encryptData(sci)
        #enc = b64encode(eci[0])
        # print "signed and encoded nonce: " + enc
        return enc
