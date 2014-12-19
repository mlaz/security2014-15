import PyKCS11
import getopt
import sys
import platform

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
	
def sign(toSign=None, pin=None, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"
	if pin == None:
		pin = 6214
		pin_available = True
		
	sign = True

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
				#print "login failed: ", str(sys.exc_info()[1])

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
			
def verify(original, signed, pin=None, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"
	if pin == None:
		pin = 6214
		pin_available = True

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
						print "Decrypted: ", d[-20:]

						if original == d[-20:]:
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

def getPubCert(pin=None, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"
	if pin == None:
		pin = 6214
	pin_available = True

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


def getPubKey(pin=None, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"
	if pin == None:
		pin = 6214
	pin_available = True

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


def getCertList(pin=None, lib=None):
	if lib == None:
		lib = "/usr/local/lib/libpteidpkcs11.so"
	if pin == None:
		pin = 6214
	pin_available = True

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
				i = 0
				attr = session.getAttributeValue(obj, all_attr)
				attrDict = dict(zip(all_attr, attr))
				
				for q, a in zip(all_attr, attr):
					if attrDict[PyKCS11.CKA_CLASS] == PyKCS11.CKO_CERTIFICATE:
						if attrDict[PyKCS11.CKA_LABEL] == labels[0] and session.isBin(q):
							i += 1
							if a and i == 3:
								certList.append(labels[0])
								certList.append(dump(''.join(map(chr, a)), 16))
								
				for q, a in zip(all_attr, attr):
					if attrDict[PyKCS11.CKA_CLASS] == PyKCS11.CKO_CERTIFICATE:
						if attrDict[PyKCS11.CKA_LABEL] == labels[1] and session.isBin(q):
							i += 1
							if a and i == 3:
								certList.append(labels[1])
								certList.append(dump(''.join(map(chr, a)), 16))
				
				for q, a in zip(all_attr, attr):
					if attrDict[PyKCS11.CKA_CLASS] == PyKCS11.CKO_CERTIFICATE:
						if attrDict[PyKCS11.CKA_LABEL] == labels[2] and session.isBin(q):
							i += 1
							if a and i == 3:
								certList.append(labels[2])
								certList.append(dump(''.join(map(chr, a)), 16))
								
				for q, a in zip(all_attr, attr):
					if attrDict[PyKCS11.CKA_CLASS] == PyKCS11.CKO_CERTIFICATE:
						if attrDict[PyKCS11.CKA_LABEL] == labels[3] and session.isBin(q):
							i += 1
							if a and i == 3:
								certList.append(labels[3])
								certList.append(dump(''.join(map(chr, a)), 16))
						
			if pin_available:
				try:
					session.logout()
				except:
					pass

			session.closeSession()
			return certList

		except PyKCS11.PyKCS11Error, e:
			print "Error: ", e
