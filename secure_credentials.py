from cryptography.fernet import Fernet
import json
import os

# File Paths
KEY_FILE_PATH = "\\Python Workspace\\NexThink Project\\key.key"
CREDENTIALS_FILE_PATH = "\\Python Workspace\\NexThink Project\\credentials.json"

def load_encryption_key():
    """Loads the encryption key from the key file."""
    if not os.path.exists(KEY_FILE_PATH):
        raise FileNotFoundError(f"Error: Key file not found at {KEY_FILE_PATH}")

    with open(KEY_FILE_PATH, "rb") as key_file:
        return key_file.read()

def decrypt_credentials():
    """Loads and decrypts the credentials."""
    if not os.path.exists(CREDENTIALS_FILE_PATH):
        raise FileNotFoundError(f"Error: Credentials file not found at {CREDENTIALS_FILE_PATH}")

    key = load_encryption_key()
    cipher = Fernet(key)

    with open(CREDENTIALS_FILE_PATH, "r") as cred_file:
        encrypted_credentials = json.load(cred_file)

    decrypted_credentials = {
        "client_id": cipher.decrypt(encrypted_credentials["client_id"].encode()).decode(),
        "client_secret": cipher.decrypt(encrypted_credentials["client_secret"].encode()).decode()
    }
    
    return decrypted_credentials