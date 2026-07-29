"""Symmetric encryption for values stored in the `credentials` table.

Both the backend (writes credentials from the admin dashboard) and the worker
(reads them to call Groq) share this so a credential encrypted by one is
readable by the other, keyed off the same CREDENTIALS_ENCRYPTION_KEY env var.
"""
from __future__ import annotations

import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


class CredentialEncryptionError(RuntimeError):
    pass


@lru_cache
def _fernet() -> Fernet:
    key = os.environ.get("CREDENTIALS_ENCRYPTION_KEY")
    if not key:
        raise CredentialEncryptionError(
            "CREDENTIALS_ENCRYPTION_KEY is not set. Generate one with "
            "`python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"` "
            "and set it identically in backend/.env and worker/.env."
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise CredentialEncryptionError(f"CREDENTIALS_ENCRYPTION_KEY is not a valid Fernet key: {exc}") from exc


def encrypt_value(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise CredentialEncryptionError(
            "Could not decrypt credential — CREDENTIALS_ENCRYPTION_KEY mismatch or corrupted value."
        ) from exc
