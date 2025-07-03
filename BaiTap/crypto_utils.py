
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import os

KEY_FOLDER = "keys"
PRIVATE_KEY_FILE = os.path.join(KEY_FOLDER, "private.pem")
PUBLIC_KEY_FILE = os.path.join(KEY_FOLDER, "public.pem")

def generate_keys():
    if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()

        os.makedirs(KEY_FOLDER, exist_ok=True)
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_key)
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(public_key)

def encrypt_file(input_path, output_path):
    key = get_random_bytes(32)
    cipher = AES.new(key, AES.MODE_EAX)
    with open(input_path, "rb") as f:
        data = f.read()
    ciphertext, tag = cipher.encrypt_and_digest(data)
    with open(output_path, "wb") as f:
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)
    return key

def decrypt_file(input_path, output_path, key):
    with open(input_path, "rb") as f:
        nonce = f.read(16)
        tag = f.read(16)
        ciphertext = f.read()
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    data = cipher.decrypt_and_verify(ciphertext, tag)
    with open(output_path, "wb") as f:
        f.write(data)

def sign_data(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    key = RSA.import_key(open(PRIVATE_KEY_FILE).read())
    h = SHA256.new(data)
    signature = pkcs1_15.new(key).sign(h)
    return signature

def verify_signature(data, signature):
    key = RSA.import_key(open(PUBLIC_KEY_FILE).read())
    h = SHA256.new(data)
    try:
        pkcs1_15.new(key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False
