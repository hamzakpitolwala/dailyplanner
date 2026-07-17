import hashlib

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return _pwd_context.hash(password)


def _verify_legacy_pbkdf2(password: str, hashed: str) -> bool:
    """Verify against the old ``pbkdf2_sha256$salt$digest`` format."""
    try:
        _, salt, expected = hashed.split("$", 2)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()
    return digest == expected


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plain-text password against its hash.

    Supports both the current bcrypt format and the legacy PBKDF2 format
    for backward compatibility with existing users.
    """
    if hashed.startswith("pbkdf2_sha256$"):
        return _verify_legacy_pbkdf2(password, hashed)
    return _pwd_context.verify(password, hashed)