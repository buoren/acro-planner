"""
Validation utilities.
"""

import re
from typing import Optional


def is_valid_email(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email string to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> Optional[str]:
    """
    Validate password strength and return error message if invalid.
    
    Args:
        password: Password to validate
        
    Returns:
        None if valid, error message string if invalid
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return "Password must contain at least one digit"
    
    return None


def sanitize_name(name: str) -> str:
    """
    Sanitize and format a name string.
    
    Args:
        name: Raw name string
        
    Returns:
        Cleaned and formatted name
    """
    # Remove extra whitespace and strip
    cleaned = re.sub(r'\s+', ' ', name.strip())
    
    # Capitalize first letter of each word
    return cleaned.title()


def validate_ulid(ulid_str: str) -> bool:
    """
    Validate ULID format.
    
    Args:
        ulid_str: ULID string to validate
        
    Returns:
        True if valid ULID format, False otherwise
    """
    # ULID should be 26 characters, base32 encoded
    if len(ulid_str) != 26:
        return False
    
    # Check if all characters are valid base32 (Crockford's Base32)
    valid_chars = set('0123456789ABCDEFGHJKMNPQRSTVWXYZ')
    return all(c in valid_chars for c in ulid_str.upper())