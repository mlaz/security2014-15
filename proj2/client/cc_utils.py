import PyKCS11
import sys
import platform
from M2Crypto import X509

# This paths must be changed before the final commit
ecraiz_cert = "../server/certificates/ECRaizEstado.crt"
cc_cert1 = "../server/certificates/Cartao de Cidadao 001.cer"
cc_cert2 = "../server/certificates/Cartao de Cidadao 002.cer"

ASN1_UTF8_FLGS = 0x10 #ASN1_STRFLGS_UTF8_CONVERT

# Auxiliar functions
def _os2str(os):
	return ''.join(chr(c) for c in os)

def hexx(intval):
	x = hex(intval)[2:]
	if (x[-1:].upper() == 'L'):
		x = x [:-1]
	if len(x) % 2 != 0:
		return "0%s" % x
	return x

def dump(src, length=8):
	result = ''
	N = 0
	while src:
		s, src = src[:length], src[length:]
		hexa = ''.join(["%02X" % ord(x) for x in s])
		result += "%s" % (hexa)
		N += length
	return result

'''Function to sign a given string with the user's
   private signature key
   toSign - the object to be signed
   pin - pin to login into the card session
   lib - pykcs11 lib
   returns the signed data'''
   	
def sign(pin, toSign=None, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"

	pkcs11 = PyKCS11.PyKCS11Lib()
	pkcs11.load(lib)

	slots = pkcs11.getSlotList()

	for s in slots:
		try:
			session = pkcs11.openSession(s)
			try:
				session.login(pin)
			except:
				pass

			objects = session.findObjects()
		
			all_attr = PyKCS11.CKA.keys()
			#remover os atributos privados
			all_attr.remove(PyKCS11.CKA_PRIVATE_EXPONENT)
			all_attr.remove(PyKCS11.CKA_PRIME_1)
			all_attr.remove(PyKCS11.CKA_PRIME_2)
			all_attr.remove(PyKCS11.CKA_EXPONENT_1)
			all_attr.remove(PyKCS11.CKA_EXPONENT_2)
			all_attr.remove(PyKCS11.CKA_COEFFICIENT)
			#usar apenas os valores int
			all_attr = [e for e in all_attr if isinstance(e, int)]

			for obj in objects:
				attr = session.getAttributeValue(obj, all_attr)
				attrDict = dict(zip(all_attr, attr))
				if attrDict[PyKCS11.CKA_CLASS] == PyKCS11.CKO_PRIVATE_KEY \
				   and attrDict[PyKCS11.CKA_KEY_TYPE] == PyKCS11.CKK_RSA \
				   and attrDict[PyKCS11.CKA_LABEL] == "CITIZEN SIGNATURE KEY":
						try:
							if toSign == None:
								toSign = "12345678901234567890"
							print "Data to be signed: ", toSign
							sig = session.sign(obj, toSign)
							return  dump(''.join(map(chr, sig)), 16)
						except:
							print "Sign failed, exception: ", str(sys.exc_info()[1])

			try:
				session.logout()
			except:
				pass

			session.closeSession()

		except PyKCS11.PyKCS11Error, e:
			print "Error: ", e

'''Function to verify the signature of user
   Receives the original and the signed object,
   searches for the Citizen Signature Key and 
   verifies the signature. Also receives the pin
   of the card and the lib to access PyKCS11
   Returns True if signature verified or False
   otherwise.'''			
   
def verify(original, signed, pin, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"

	x = len(original)
	print x

	pkcs11 = PyKCS11.PyKCS11Lib()
	pkcs11.load(lib)

	slots = pkcs11.getSlotList()

	for s in slots:
		try:
			session = pkcs11.openSession(s)
			try:
				session.login(pin)
			except:
				pass
				
			objects = session.findObjects()
		
			all_attr = PyKCS11.CKA.keys()
			#remover os atributos privados
			all_attr.remove(PyKCS11.CKA_PRIVATE_EXPONENT)
			all_attr.remove(PyKCS11.CKA_PRIME_1)
			all_attr.remove(PyKCS11.CKA_PRIME_2)
			all_attr.remove(PyKCS11.CKA_EXPONENT_1)
			all_attr.remove(PyKCS11.CKA_EXPONENT_2)
			all_attr.remove(PyKCS11.CKA_COEFFICIENT)
			#usar apenas os valores int
			all_attr = [e for e in all_attr if isinstance(e, int)]

			for obj in objects:
				attr = session.getAttributeValue(obj, all_attr)
				attrDict = dict(zip(all_attr, attr))
				if attrDict[PyKCS11.CKA_CLASS] == PyKCS11.CKO_PRIVATE_KEY \
				   and attrDict[PyKCS11.CKA_KEY_TYPE] == PyKCS11.CKK_RSA \
				   and attrDict[PyKCS11.CKA_LABEL] == "CITIZEN SIGNATURE KEY":
					mod = attrDict[PyKCS11.CKA_MODULUS]
					exp = attrDict[PyKCS11.CKA_PUBLIC_EXPONENT]
					if mod and exp:
						mx = eval('0x%s' % ''.join(chr(c) for c in mod).encode('hex'))
						ex = eval('0x%s' % ''.join(chr(c) for c in exp).encode('hex'))
						print "Verifying using following Pub Key:"
						print "Modulus: ", dump(''.join(map(chr, mod)), 16)
						print "Exponent: ", dump(''.join(map(chr, exp)), 16)
						sx = eval('0x%s' % signed)
						decrypted = pow(sx, ex, mx)
						print "Original: ", original
						d = hexx(decrypted).decode('hex')
						print "Decrypted: ", d[-x:]

						if original == d[-x:]:
							print "Sig verified"
							return True
						else:
							print "Sig not verified"

			try:
				session.logout()
			except:
				pass

			session.closeSession()
			return False

		except PyKCS11.PyKCS11Error, e:
			print "Error: ", e

'''Function to retrive the Public Key from a CC
   Receives the pin for the card and the lib to
   access PyKCS11. Returns an hexadecimal string
   with the value of the PubKey'''

def getPubCert(pin, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"

	pkcs11 = PyKCS11.PyKCS11Lib()
	pkcs11.load(lib)

	slots = pkcs11.getSlotList()

	for s in slots:
		try:
			session = pkcs11.openSession(s)
			try:
				session.login(pin)
			except:
				pass

			objects = session.findObjects()

			
			all_attr = PyKCS11.CKA.keys()
			#remover os atributos privados
			all_attr.remove(PyKCS11.CKA_PRIVATE_EXPONENT)
			all_attr.remove(PyKCS11.CKA_PRIME_1)
			all_attr.remove(PyKCS11.CKA_PRIME_2)
			all_attr.remove(PyKCS11.CKA_EXPONENT_1)
			all_attr.remove(PyKCS11.CKA_EXPONENT_2)
			all_attr.remove(PyKCS11.CKA_COEFFICIENT)
			#usar apenas os valores int
			all_attr = [e for e in all_attr if isinstance(e, int)]

			for obj in objects:
				attr = session.getAttributeValue(obj, all_attr)
				attrDict = dict(zip(all_attr, attr))
				i = 0
				for q, a in zip(all_attr, attr):
					if attrDict[PyKCS11.CKA_CLASS] == PyKCS11.CKO_PUBLIC_KEY \
					   and session.isBin(q):
						i += 1
						if a and i == 3:
							return dump(''.join(map(chr, a)), 16)
			
			if pin_available:
				try:
					session.logout()
				except:
					pass
			session.closeSession()

		except PyKCS11.PyKCS11Error, e:
			print "Error: ", e

'''Function to get the Public Key of a CC in the format
   exponent and modulus, similar to prof. Zuquete ccpam's
   module. Returns a list with two hexadecimal strings'''

def getPubKey(pin, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"

	pkcs11 = PyKCS11.PyKCS11Lib()
	pkcs11.load(lib)

	slots = pkcs11.getSlotList()

	for s in slots:
		try:
			session = pkcs11.openSession(s)
			try:
				session.login(pin)
			except:
				pass

			objects = session.findObjects()

			
			all_attr = PyKCS11.CKA.keys()
			#remover os atributos privados
			all_attr.remove(PyKCS11.CKA_PRIVATE_EXPONENT)
			all_attr.remove(PyKCS11.CKA_PRIME_1)
			all_attr.remove(PyKCS11.CKA_PRIME_2)
			all_attr.remove(PyKCS11.CKA_EXPONENT_1)
			all_attr.remove(PyKCS11.CKA_EXPONENT_2)
			all_attr.remove(PyKCS11.CKA_COEFFICIENT)
			#usar apenas os valores int
			all_attr = [e for e in all_attr if isinstance(e, int)]

			for obj in objects:
				attr = session.getAttributeValue(obj, all_attr)
				attrDict = dict(zip(all_attr, attr))
				i = 0
				for q, a in zip(all_attr, attr):
					if attrDict[PyKCS11.CKA_CLASS] == PyKCS11.CKO_PUBLIC_KEY \
					   and attrDict[PyKCS11.CKA_KEY_TYPE] == PyKCS11.CKK_RSA:
						m = attrDict[PyKCS11.CKA_MODULUS]
						e = attrDict[PyKCS11.CKA_PUBLIC_EXPONENT]
						return [dump(''.join(map(chr, e)), 16), dump(''.join(map(chr, m)), 16)]
			
			if pin_available:
				try:
					session.logout()
				except:
					pass

			session.closeSession()

		except PyKCS11.PyKCS11Error, e:
			print "Error: ", e
			
'''Function to get a list of the certificates in the CC
   Receives the pin for the card and the lib to access
   PyKCS11 and returns a list of four X509 certificates'''
			
def getCertList(pin, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"

	pkcs11 = PyKCS11.PyKCS11Lib()
	pkcs11.load(lib)

	slots = pkcs11.getSlotList()

	certList = []
	labels = ["CITIZEN AUTHENTICATION CERTIFICATE", "AUTHENTICATION SUB CA", "CITIZEN SIGNATURE CERTIFICATE", "SIGNATURE SUB CA"]

	for s in slots:
		try:
			session = pkcs11.openSession(s)
			try:
				session.login(pin)
			except:
				pass

			objects = session.findObjects()
			certificates = []
			
			for obj in objects:
				d = obj.to_dict()
				if d['CKA_CLASS'] == 'CKO_CERTIFICATE':
					der = _os2str(d['CKA_VALUE'])
					cert = X509.load_cert_string(der, X509.FORMAT_DER)
					certificates.append(cert)
			return certificates
						
			if pin_available:
				try:
					session.logout()
				except:
					pass

			session.closeSession()
			return certList

		except PyKCS11.PyKCS11Error, e:
			print "Error: ", e

'''Function to convert the certificates to dict
   Must likely will be erased for the final commit'''

def certToDict(label, pin, lib=None):
# list of labels used by the ptCC: ["CITIZEN AUTHENTICATION CERTIFICATE", 
# "AUTHENTICATION SUB CA", "CITIZEN SIGNATURE CERTIFICATE", "SIGNATURE SUB CA"]
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"

	pkcs11 = PyKCS11.PyKCS11Lib()
	pkcs11.load(lib)

	slots = pkcs11.getSlotList()

	for s in slots:
		try:
			session = pkcs11.openSession(s)
			try:
				session.login(pin)
			except:
				pass
				
			objects = session.findObjects()
		
			all_attr = PyKCS11.CKA.keys()
			#remover os atributos privados
			all_attr.remove(PyKCS11.CKA_PRIVATE_EXPONENT)
			all_attr.remove(PyKCS11.CKA_PRIME_1)
			all_attr.remove(PyKCS11.CKA_PRIME_2)
			all_attr.remove(PyKCS11.CKA_EXPONENT_1)
			all_attr.remove(PyKCS11.CKA_EXPONENT_2)
			all_attr.remove(PyKCS11.CKA_COEFFICIENT)
			#usar apenas os valores int
			all_attr = [e for e in all_attr if isinstance(e, int)]
			data_dict = {}

			for obj in objects:
				attr = session.getAttributeValue(obj, all_attr)
				attrDict = dict(zip(all_attr, attr))
				if attrDict[PyKCS11.CKA_LABEL] == label and attrDict[PyKCS11.CKA_CLASS] == PyKCS11.CKO_CERTIFICATE:
					data_dict.update({label: PyKCS11.CK_OBJECT_HANDLE.to_dict(obj)})

			try:
				session.logout()
			except:
				pass

			session.closeSession()
			return data_dict

		except PyKCS11.PyKCS11Error, e:
			print "Error: ", e

'''Function to verify the chain of trust between certificates
   Receives two X509 certificates (run the getCertList function
   first) and returns True if the chain is verified and False
   otherwise.
   If the getCertList function is called before, the function
   must return True with the pairs 0/1 and 2/3 of the list
   returned by that function'''
   
# THIS FUNCTION MUST BE ON THE SERVER SIDE

def certChain(cert, sub_ca):
	ecraiz = X509.load_cert(ecraiz_cert)
	
	if "001" not in sub_ca.get_issuer().as_text():
		cccert = X509.load_cert(cc_cert2, format=0)
	else:
		cccert = X509.load_cert(cc_cert1, format=0)
	
	t1 = False
	
	if sub_ca.get_subject().as_text() == cert.get_issuer().as_text():
		pkey = sub_ca.get_pubkey()
		if not cert.verify(pkey):
			return False
		elif cccert.get_subject().as_text() == sub_ca.get_issuer().as_text():
			pkey = cccert.get_pubkey()
			if not sub_ca.verify(pkey):
				return False
			elif ecraiz.get_subject().as_text() == cccert.get_issuer().as_text():
				pkey = ecraiz.get_pubkey()
				if cccert.verify(pkey):
					if ecraiz.verify(pkey):
						return True
	
	return False
