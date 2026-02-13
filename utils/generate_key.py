# Save this as generate_key.py
from cryptography.fernet import Fernet

key = Fernet.generate_key().decode()
print("Add this to GitHub Secrets as ARTIFACT_ENCRYPTION_KEY:")
print(key)