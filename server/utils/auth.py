"""
Authentication and security utilities.
"""

import hashlib
import secrets
from typing import Tuple


def generate_salt() -> str:
    """Generate a random salt for password hashing."""
    return secrets.token_hex(32)


def hash_password(password: str, salt: str) -> str:
    """
    Hash a password with salt using SHA-256.
    
    Args:
        password: Plain text password
        salt: Salt string
        
    Returns:
        Hashed password string
    """
    # Combine password and salt
    salted_password = password + salt
    
    # Hash using SHA-256
    hash_object = hashlib.sha256(salted_password.encode())
    return hash_object.hexdigest()


def create_password_hash(password: str) -> Tuple[str, str]:
    """
    Create a password hash with a new salt.
    
    Args:
        password: Plain text password
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    salt = generate_salt()
    password_hash = hash_password(password, salt)
    return password_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verify a password against stored hash and salt.
    
    Args:
        password: Plain text password to verify
        stored_hash: Stored password hash
        salt: Salt used for the stored hash
        
    Returns:
        True if password matches, False otherwise
    """
    test_hash = hash_password(password, salt)
    return test_hash == stored_hash