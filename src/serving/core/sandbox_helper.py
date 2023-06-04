import base64
import sandbox

#sandbox._generate_rsa_pair(1024)
#sandbox._generate_rsa_pair(2048)
#sdi = sandbox.default_device_serial()
original_password = bytes("ligo", 'utf-8')
sdi = original_password
digest = sandbox.sha256_digest(sdi)
print("sdi:", digest)

ret = sandbox._encrypt_by_public(digest, "./public.pem")
b64key = base64.b64encode(ret)
print("b64(enc(sdi)):", b64key)

ret = sandbox.sha256_recover(b64key, "./private.pem")
sandbox._encrypt(ret, "model", "model_core")
sandbox._decrypt(ret, "model_core", "model_dore")
"""
"""
