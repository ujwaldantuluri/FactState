import ssl
import socket
from datetime import datetime

def check_ssl_certificate(domain):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                valid_from = datetime.strptime(cert['notBefore'], "%b %d %H:%M:%S %Y %Z")
                valid_to = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                issuer = cert.get('issuer', [])
                subject = cert.get('subject', [])
                return {
                    "valid_from": str(valid_from),
                    "valid_to": str(valid_to),
                    "issuer": issuer,
                    "subject": subject,
                    "is_valid": datetime.utcnow() < valid_to
                }
    except Exception as e:
        return {
            "valid_from": None,
            "valid_to": None,
            "issuer": None,
            "subject": None,
            "is_valid": False,
            "error": str(e)
        }

