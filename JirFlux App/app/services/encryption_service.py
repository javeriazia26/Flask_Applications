import os
import hashlib

from cryptography.fernet import Fernet
from flask import current_app


def get_cipher():
    key = current_app.config["ENCRYPTION_KEY"].encode()
    return Fernet(key)


def encrypt_data(data):
    
    if not data:
        return None

    cipher = get_cipher()
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data):
    if not encrypted_data:
        return None

    cipher = get_cipher()
    return cipher.decrypt(encrypted_data.encode()).decode()


def hash_data(data):
    if not data:
        return None

    return hashlib.sha256(data.encode()).hexdigest()
