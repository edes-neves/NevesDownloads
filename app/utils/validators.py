import re


def is_valid_url(url: str) -> bool:
    """
    Valida se a string parece uma URL HTTP/HTTPS.
    """
    if not url:
        return False
    url = url.strip()
    pattern = re.compile(r"^https?://", re.IGNORECASE)
    return bool(pattern.match(url))
