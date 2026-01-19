"""Security utilities for authentication and password hashing."""
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Optional

import bcrypt as bcrypt_lib
from jose import JWTError, jwt

from vibeify_api.core.config import get_settings

settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    # Always pre-hash with SHA256 to avoid bcrypt's 72-byte limit
    password_bytes = plain_password.encode('utf-8')
    sha256_hash_bytes = hashlib.sha256(password_bytes).digest()  # Use digest() to get bytes, not hexdigest()
    return bcrypt_lib.checkpw(sha256_hash_bytes, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    # Always pre-hash with SHA256 to avoid bcrypt's 72-byte limit
    # This ensures consistent behavior regardless of password length
    password_bytes = password.encode('utf-8')
    # Use digest() to get raw bytes (32 bytes) instead of hexdigest() (64 hex chars = 64 bytes)
    sha256_hash_bytes = hashlib.sha256(password_bytes).digest()
    # Use bcrypt library directly with bytes (32 bytes from SHA256 digest)
    hashed = bcrypt_lib.hashpw(sha256_hash_bytes, bcrypt_lib.gensalt())
    return hashed.decode('utf-8')  # Convert back to string for storage


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token (e.g., {"sub": "user_id"})
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
