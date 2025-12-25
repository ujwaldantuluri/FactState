from urllib.parse import urlparse

def normalize_url(url: str) -> str:
    p = urlparse(url)
    scheme = p.scheme or "https"
    netloc = p.netloc.lower()
    path = p.path.rstrip("/")
    return f"{scheme}://{netloc}{path}"
