"""ECDH P-384 + AES-GCM-256 cryptographic helpers for Broadcast+ authentication.

Implements the key exchange and password encryption protocol matching
Broadcast+.exe ``app.asar`` logic (``buildEncryptedResult``).
"""

from __future__ import annotations

import base64
import hashlib
import os

import httpx
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDH,
    SECP384R1,
    generate_private_key,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_der_public_key,
)

from .._core.constants import PLUS_BASE_URL


def do_key_exchange(client: httpx.Client, headers: dict[str, str]) -> tuple[bytes, str]:
    """ECDH P-384 key exchange with Broadcast+ server.

    Args:
        client: httpx.Client instance for the HTTP call.
        headers: Request headers (content-type, accept, x-version).

    Returns:
        Tuple of (aes_key_32_bytes, session_id_base64_str).
    """
    private_key = generate_private_key(SECP384R1())
    pub_der = private_key.public_key().public_bytes(
        Encoding.DER, PublicFormat.SubjectPublicKeyInfo
    )

    r = client.post(
        f"{PLUS_BASE_URL}/authentication/v1/key-exchange",
        json={"publicKey": base64.b64encode(pub_der).decode()},
        headers=headers,
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()

    server_pub = load_der_public_key(base64.b64decode(data["publicKey"]))
    session_id: str = data["sessionId"]

    # SHA-256 of the ECDH shared secret -> 32-byte AES key (matches app.asar logic)
    shared = private_key.exchange(ECDH(), server_pub)
    aes_key = hashlib.sha256(shared).digest()
    return aes_key, session_id


def encrypt_password(password: str, aes_key: bytes, session_id: str) -> str:
    """AES-GCM-256 password encryption matching Broadcast+ ``buildEncryptedResult()``.

    Format: ``base64(session_id_bytes + iv_12 + ciphertext_with_gcm_tag)``

    Args:
        password: Plaintext password.
        aes_key: 32-byte AES key from :func:`do_key_exchange`.
        session_id: Base64-encoded session ID from :func:`do_key_exchange`.

    Returns:
        Base64-encoded encrypted payload ready for the login request body.
    """
    iv = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(iv, password.encode("utf-8"), None)
    session_bytes = base64.b64decode(session_id)
    return base64.b64encode(session_bytes + iv + ciphertext).decode()
