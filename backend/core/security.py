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


import hmac
import time
from backend.core.config import settings


def generate_oauth_state(user_id: str) -> str:
    """Generate a cryptographically signed HMAC token for OAuth state parameter."""
    timestamp = str(int(time.time()))
    msg = f"{user_id}:{timestamp}".encode("utf-8")
    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return f"{user_id}:{timestamp}:{sig}"


def verify_oauth_state(state: str, max_age_seconds: int = 600) -> str | None:
    """Verify an OAuth state token signature and expiration. Returns user_id if valid, else None."""
    if not state:
        return None
    parts = state.split(":")
    if len(parts) != 3:
        return None

    user_id, timestamp_str, sig = parts
    try:
        ts = int(timestamp_str)
        if (int(time.time()) - ts) > max_age_seconds:
            return None
    except ValueError:
        return None

    msg = f"{user_id}:{timestamp_str}".encode("utf-8")
    expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig, expected_sig):
        return user_id
    return None