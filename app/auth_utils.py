# app/auth_utils.py

from pwdlib import PasswordHash

# Unify the application to use pwdlib consistently (modern standard replacing passlib)
pwd_context = PasswordHash.recommended()

def hash(password: str) -> str:
    return pwd_context.hash(password)

def verify(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)