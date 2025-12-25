from __future__ import annotations
import ssl, socket, datetime, hashlib
from dataclasses import dataclass
from typing import Optional

@dataclass
class TLSInfo:
    days_remaining: Optional[int]
    issuer: str | None
    san_mismatch: bool
    sig_hash: str | None
    errors: list[str]

def fetch_tls_info(host: str, port: int = 443, timeout: float = 3.5) -> TLSInfo:
    errors: list[str] = []
    issuer = None
    days_remaining: Optional[int] = None
    san_mismatch = False
    sig_hash = None
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                # Expiry
                try:
                    not_after = cert.get('notAfter')
                    if not_after:
                        dt = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        days_remaining = (dt - datetime.datetime.utcnow()).days
                except Exception as e:  # pragma: no cover
                    errors.append(f"expiry-parse:{e}")
                # Issuer
                try:
                    issuer = "/".join("=".join(x) for x in cert.get('issuer', [])[0]) if cert.get('issuer') else None
                except Exception:
                    pass
                # SAN match
                try:
                    sans = []
                    ext = cert.get('subjectAltName', [])
                    for typ, val in ext:
                        if typ == 'DNS':
                            sans.append(val.lower())
                    if sans and host.lower() not in sans and not any(_wildcard_matches(host.lower(), s) for s in sans if s.startswith('*')):
                        san_mismatch = True
                except Exception:
                    pass
                # Signature hash from cipher (approx – deeper parsing would need cryptography)
                try:
                    # Without external deps we approximate using cipher suite name
                    cipher = ssock.cipher()
                    if cipher and cipher[0]:
                        name = cipher[0].lower()
                        if 'sha256' in name:
                            sig_hash = 'sha256'
                        elif 'sha384' in name:
                            sig_hash = 'sha384'
                        elif 'sha1' in name:
                            sig_hash = 'sha1'
                        else:
                            sig_hash = None
                except Exception:
                    pass
    except Exception as e:
        errors.append(str(e))
    return TLSInfo(days_remaining=days_remaining, issuer=issuer, san_mismatch=san_mismatch, sig_hash=sig_hash, errors=errors)

def _wildcard_matches(host: str, pattern: str) -> bool:
    # pattern like *.example.com
    if not pattern.startswith('*.'):
        return False
    suffix = pattern[1:]  # .example.com
    return host.endswith(suffix)
