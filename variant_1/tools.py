from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Signature import pss
from Crypto.Util import number

from typing import Union
from voter_list import VoterList

import base64
import json
import math

def hash(message): return SHA256.new(message.encode())

def generate_key():
    key = RSA.generate(2048)
    return key, key.public_key()

def encrypt(m : bytes, public_key) -> str:
    rsa_cipher = PKCS1_OAEP.new(public_key)
    aes_key = get_random_bytes(32)
    enc_aes_key = rsa_cipher.encrypt(aes_key)

    aes_cipher = AES.new(aes_key, AES.MODE_GCM)
    ciphertext, tag = aes_cipher.encrypt_and_digest(m)

    package = {
        "enc_key": base64.b64encode(enc_aes_key).decode(),
        "nonce": base64.b64encode(aes_cipher.nonce).decode(),
        "tag": base64.b64encode(tag).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode()
    }
    return json.dumps(package)

def decrypt(package_json : str, private_key) -> str:
    package = json.loads(package_json)
    enc_key = base64.b64decode(package["enc_key"])
    nonce = base64.b64decode(package["nonce"])
    tag = base64.b64decode(package["tag"])
    ciphertext = base64.b64decode(package["ciphertext"])

    rsa_cipher = PKCS1_OAEP.new(private_key)
    aes_key = rsa_cipher.decrypt(enc_key)

    aes_cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    plaintext = aes_cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode()

def _b64_encode(b: bytes) -> str:
    return base64.b64encode(b).decode('ascii')

def _b64_decode(s: str) -> bytes:
    return base64.b64decode(s.encode('ascii'))

def generate_aes_key(size: int = 32) -> bytes:
    return get_random_bytes(size)

def aes_encrypt(plaintext: bytes, key: bytes) -> str:
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    
    return json.dumps({
        "ciphertext": _b64_encode(ciphertext),
        "nonce": _b64_encode(cipher.nonce),
        "tag": _b64_encode(tag)
    })

def aes_decrypt(json_blob: Union[str, bytes], key: bytes) -> bytes:
    if isinstance(json_blob, bytes):
        json_blob = json_blob.decode('utf-8')
    obj = json.loads(json_blob)

    ciphertext = _b64_decode(obj["ciphertext"])
    nonce = _b64_decode(obj["nonce"])
    tag = _b64_decode(obj["tag"])

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)

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

def construct_message(id : int, code : str, text : str, s_priv_key, k_pub_key) -> str:
    h = hash(text)

    signature = sign(h, s_priv_key)

    sign_string = json.dumps({
        'signature' : signature,
        'text' : text
    })
    
    encrypted = encrypt(sign_string.encode(), k_pub_key)

    return json.dumps({
        'id' : id,
        'code' : code,
        'text' : encrypted
    }).encode()

def deconstruct_message(string : str, s_pub_key, k_priv_key):
    bundle = json.loads(string)
    id = bundle['id']
    code = bundle['code']
    encrypted = bundle['text']

    if s_pub_key is None:
        v = VoterList()
        s_pub_key = v.get_public_keys()[str(id)]['public_key']

    sign_string = decrypt(encrypted, k_priv_key)
    sign_bundle = json.loads(sign_string)

    signature = sign_bundle['signature']
    text = sign_bundle['text']
    h = hash(text)

    if verify(signature, h, s_pub_key):
        return id, code, text, s_pub_key
    else:
        print('Signature invalid')
        return

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