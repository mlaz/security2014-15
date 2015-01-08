import Crypto.Hash import HMAC
from Crypto import Random

if __name__ == "__main__":
    salt = Random.get_random_bytes(Crypto.Hash.SHA256.digest_size)
    h1 = HMAC.new(salt, digestmod=Crypto.Hash.SHA256)
    h1.update(b'Hello')
    print h1.hexdigest()


