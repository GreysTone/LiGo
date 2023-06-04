"""
  Core.SandBox: Provides security related functions

  Contact: arthur.r.song@gmail.com
"""

import os
import uuid
import base64
import logging

import rsa
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256


def device_serial(serial=None):
    """Returns device serial string.

    Gets serial string of current device based on `serial`. If `serial` is not
    provided, then simply based on `uuid.getnode()`.

    Args:
        serial: A given string that used to get device serial string

    Returns:
        A string of serial string.
    """
    if serial is None:
        serial = _default_device_serial()
    logging.debug("current device serial: %s", serial)
    return sha256_digest(bytes(serial, 'utf-8'))

def _default_device_serial():
    return str(hex(uuid.getnode()))

def sha256_digest(content):
    """Converts `content` to SHA256 digest.

    Gets base64 encoded SHA256 digest string of content.

    Args:
        content: a byte string

    Returns:
        A base64 encoded digest string
    """
    return base64.b64encode(SHA256.new(content).digest())

def decode_model(a64key, pvtkey, path, inf, outf):
    key = sha256_recover(a64key, pvtkey)
    _decrypt(key, os.path.join(path, inf), os.path.join(path, outf))

def sha256_recover(content, pvt_path):
    ret = _decrypt_by_private(base64.b64decode(content), pvt_path)
    return SHA256.new(ret).digest()


def _generate_rsa_pair(keysize=1024):
    (pubkey, pvtkey) = rsa.newkeys(keysize)
    with open('public.pem', 'wb') as pubf, open('private.pem', 'wb') as pvtf:
        pubf.write(pubkey.save_pkcs1())
        pvtf.write(pvtkey.save_pkcs1())
    logging.debug(">>> generated key pairs")


def _encrypt_by_public(key, pub_file_path):
    with open(pub_file_path, 'r') as pf:
        return rsa.encrypt(key, rsa.PublicKey.load_pkcs1(pf.read()))


def _decrypt_by_private(key, pvt_file_path):
    with open(pvt_file_path, 'r') as pf:
        return rsa.decrypt(key, rsa.PrivateKey.load_pkcs1(pf.read()))


def _encrypt(sandbox_key, src_file, dest_file):
    IV = Random.new().read(AES.block_size)
    encryptor = AES.new(sandbox_key, AES.MODE_CBC, IV)
    with open(src_file, 'rb') as src, open(dest_file, 'wb') as dest:
        chunk_size = 64*1024
        file_size = str(os.path.getsize(src_file)).zfill(16)
        dest.write(bytes(file_size, 'utf-8'))
        dest.write(IV)
        while True:
            chunk = src.read(chunk_size)
            if len(chunk) == 0:
                break
            elif len(chunk) % 16 != 0:
                chunk += bytes(' ', 'utf-8')*(16 - len(chunk)%16)
            dest.write(encryptor.encrypt(chunk))

def _decrypt(sandbox_key, src_file, dest_file):
    with open(src_file, 'rb') as src, open(dest_file, 'wb') as dest:
        chunk_size = 64*1024
        file_size = int(src.read(16))
        decryptor = AES.new(sandbox_key, AES.MODE_CBC, IV=src.read(16))
        while True:
            chunk = src.read(chunk_size)
            if len(chunk)==0:
                break
            dest.write(decryptor.decrypt(chunk))
        dest.truncate(file_size)

# TODO: these functions need to be tested before use it
def _sign_by_private(key, pvt_file_path):
    with open(pvt_file_path, 'r') as pf:
        return rsa.sign(key, rsa.PrivateKey.load_pkcs1(pf.read()), 'SHA-1')

def _verify_by_public(signature, pub_file_path, verify):
    with open(pub_file_path, 'r') as pf:
        return rsa.verify(verify, signature, rsa.PublicKey.load_pkcs1(pf.read()))

