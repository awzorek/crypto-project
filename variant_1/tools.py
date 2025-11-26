from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.Signature import pss
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util import number
from binascii import hexlify, unhexlify

import base64
import json
import math

def hash(message): return SHA256.new(message)

def generate_key():
    key = RSA.generate(2048)
    return key, key.public_key()

def encrypt(m, public_key):
    cipher = PKCS1_OAEP.new(public_key)
    result = cipher.encrypt(m)
    return hexlify(result)

def decrypt(m, private_key):
    m = unhexlify(m)
    cipher = PKCS1_OAEP.new(private_key)
    result = cipher.decrypt(m)
    return result.decode('utf-8')

def sign(hash, private_key):
    signer = pss.new(private_key)
    signature = signer.sign(hash)
    return base64.b64encode(signature).decode()

def verify(signature, hash, public_key):
    verifier = pss.new(public_key)
    try:
        verifier.verify(hash, base64.b64decode(signature))
        return True
    except (ValueError, TypeError):
        return False

def int_from_bytes(b: bytes) -> int: return int.from_bytes(b, byteorder='big')
def bytes_from_int(i: int, length: int) -> bytes: return i.to_bytes(length, byteorder='big')

def blind(hash, public_key):
    # public key of the signer
    e = public_key.e
    n = public_key.n
    m = int_from_bytes(hash.digest())
    if m >= n: m = m % n

    r = n
    while math.gcd(r,n) != 1:
        r = number.getRandomRange(2, n-1)
    
    r_e = pow(r, e, n)
    # returns blinded hash of a message and a random number selected for blinding
    return (m * r_e) % n, r

def blind_sign(blinded_m, private_key):
    return pow(blinded_m, private_key.d, private_key.n)

def unblind(signed_blind, r, public_key):
    n = public_key.n
    r_inv = number.inverse(r,n)
    signed = (signed_blind * r_inv) % n
    # original hash: bytes_from_int(signed, (n.bit_length() + 7) // 8)
    return signed

def verify_blind_signature(signed, hash, public_key):
    m = int_from_bytes(hash.digest())
    return m == pow(signed, public_key.e, public_key.n)

def construct_message(id : int, code : str, text : str) -> str:
    return json.dumps({
        'id' : id,
        'code' : code,
        'text' : text
    }).encode()

def deconstruct_message(string : str):
    bundle = json.loads(string)
    return bundle['id'], bundle['code'], bundle['text']

# d,e = generate_key()
# m = b'This is a message'
# hash = hash(m)

# en = encrypt(m, e)
# print('Encrypted:',en)
# de = decrypt(en,d)
# print('Decrypted:',de)

# signature = sign(hash, d)
# print('Signed:', signature)
# print('Verified:', verify(signature, hash, e))

# blinded, r = blind(hash, e)
# bs = blind_sign(blinded, d)
# s = unblind(bs, r, e)
# print('Verification:', verify_blind_signature(s, hash, e))