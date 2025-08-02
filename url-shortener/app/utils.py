import re
import random
import string
from urllib.parse import urlparse
from typing import Tuple

def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate if a URL is properly formatted
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"
    
    # Check if URL has a scheme
    if not url.startswith(('http://', 'https://')):
        return False, "URL must start with http:// or https://"
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, "Invalid URL format"
        
        # Basic domain validation
        if len(parsed.netloc) < 3:
            return False, "Invalid domain name"
        
        return True, ""
    except Exception:
        return False, "Invalid URL format"

def generate_short_code(length: int = 6) -> str:
    """
    Generate a random alphanumeric short code
    
    Args:
        length: Length of the short code (default: 6)
        
    Returns:
        Random alphanumeric string
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_unique_short_code(store, length: int = 6, max_attempts: int = 10) -> str:
    """
    Generate a unique short code that doesn't exist in the store
    
    Args:
        store: URLStore instance to check against
        length: Length of the short code
        max_attempts: Maximum attempts to generate unique code
        
    Returns:
        Unique short code
        
    Raises:
        RuntimeError: If unable to generate unique code after max attempts
    """
    for _ in range(max_attempts):
        short_code = generate_short_code(length)
        if not store.url_exists(short_code):
            return short_code
    
    raise RuntimeError(f"Unable to generate unique short code after {max_attempts} attempts")

def sanitize_url(url: str) -> str:
    """
    Sanitize URL by trimming whitespace and ensuring proper format
    
    Args:
        url: URL to sanitize
        
    Returns:
        Sanitized URL
    """
    return url.strip()

def format_short_url(short_code: str, base_url: str = "http://localhost:5000") -> str:
    """
    Format the complete short URL
    
    Args:
        short_code: The short code
        base_url: Base URL for the service
        
    Returns:
        Complete short URL
    """
    return f"{base_url.rstrip('/')}/{short_code}"