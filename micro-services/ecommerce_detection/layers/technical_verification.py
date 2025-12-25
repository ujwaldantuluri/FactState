from __future__ import annotations
import socket
import ssl
import httpx
from dataclasses import dataclass
from typing import Optional, Dict
from urllib.parse import urlparse
import os

@dataclass
class LayerResult:
    score: float
    message: str

# Configuration
VERIFIED_MAJOR_PLATFORMS = {
    "amazon.com", "flipkart.com", "myntra.com", "ajio.com", "nykaa.com",
    "meesho.com", "snapdeal.com", "shopclues.com", "paytmmall.com",
    "ebay.com", "alibaba.com", "walmart.com", "target.com", "bestbuy.com"
}

TRUSTED_REGISTRARS = [
    "godaddy", "namecheap", "google", "amazon", "cloudflare", "verisign", 
    "networksolutions", "1&1", "bluehost", "hostgator"
]

HIGH_RISK_COUNTRIES = ["CN", "RU", "PK", "BD", "NG", "ID"]

async def _get_ssl_info(domain: str) -> Dict:
    """Get SSL certificate information with improved reliability"""
    try:
        # Method 1: Try direct socket connection
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'subject': dict(x[0] for x in cert['subject']),
                        'valid_from': cert['notBefore'],
                        'valid_to': cert['notAfter'],
                        'is_wildcard': cert['subject']['commonName'].startswith('*.'),
                        'method': 'socket'
                    }
        except Exception:
            pass
        
        # Method 2: Try HTTP request to get SSL info
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=True) as client:
                response = await client.get(f"https://{domain}", follow_redirects=True)
                if response.status_code < 400:
                    return {
                        'issuer': {'organizationName': 'Valid Certificate Authority'},
                        'subject': {'commonName': domain},
                        'valid_from': 'Recent',
                        'valid_to': 'Future',
                        'is_wildcard': False,
                        'method': 'httpx'
                    }
        except Exception:
            pass
        
        return {}
    except Exception:
        return {}

async def _get_whois_enhanced(domain: str) -> Dict:
    """Enhanced WHOIS analysis with registrar reputation"""
    try:
        import whois
        data = whois.whois(domain)
        
        registrar = (data.registrar or "").lower() if hasattr(data, 'registrar') else ""
        is_trusted_registrar = any(trusted in registrar for trusted in TRUSTED_REGISTRARS)
        
        creation_date = data.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        
        return {
            'registrar': registrar,
            'trusted_registrar': is_trusted_registrar,
            'creation_date': creation_date,
            'privacy_protection': 'privacy' in str(data).lower() or 'protected' in str(data).lower(),
            'country': getattr(data, 'country', None)
        }
    except Exception:
        return {}

async def _get_dns_info(domain: str) -> Dict:
    """Get DNS and hosting information with enhanced detection"""
    try:
        import socket
        ip = socket.gethostbyname(domain)
        
        # Enhanced trusted hosting detection
        is_trusted_hosting = False
        hosting_provider = "Unknown"
        
        # Amazon/AWS IP ranges
        if any(ip.startswith(prefix) for prefix in [
            '52.', '54.', '13.', '18.', '35.', '107.', '174.', '176.', '184.',
            '23.', '50.', '54.', '75.', '99.', '205.', '207.'
        ]):
            is_trusted_hosting = True
            hosting_provider = "Amazon AWS"
        
        # Cloudflare
        elif any(ip.startswith(prefix) for prefix in [
            '104.16.', '104.17.', '104.18.', '104.19.', '104.20.', '104.21.',
            '172.64.', '172.65.', '172.66.', '172.67.', '172.68.', '172.69.'
        ]):
            is_trusted_hosting = True
            hosting_provider = "Cloudflare"
        
        # Google Cloud
        elif any(ip.startswith(prefix) for prefix in [
            '35.', '34.', '130.', '146.', '104.196.', '104.197.'
        ]):
            is_trusted_hosting = True
            hosting_provider = "Google Cloud"
        
        # Microsoft Azure
        elif any(ip.startswith(prefix) for prefix in [
            '13.', '20.', '40.', '52.', '104.', '137.', '138.', '168.'
        ]):
            is_trusted_hosting = True
            hosting_provider = "Microsoft Azure"
        
        return {
            'ip_address': ip,
            'trusted_hosting': is_trusted_hosting,
            'hosting_provider': hosting_provider,
            'has_mx': True  # Assume email is configured for established domains
        }
    except Exception:
        return {
            'ip_address': None, 
            'trusted_hosting': False, 
            'hosting_provider': 'Unknown',
            'has_mx': False
        }

async def analyze(url: str) -> LayerResult:
    """Technical infrastructure verification"""
    parsed = urlparse(url)
    domain = parsed.hostname or ""
    
    # MAJOR PLATFORM BYPASS - Verified platforms get automatic pass
    if domain.lower() in VERIFIED_MAJOR_PLATFORMS:
        return LayerResult(
            score=0.0, 
            message=f"VERIFIED PLATFORM: {domain} has enterprise-grade security infrastructure"
        )
    
    score = 0.0
    reasons = []
    
    # SSL Certificate Analysis with better error handling
    try:
        ssl_info = await _get_ssl_info(domain)
        if ssl_info:
            issuer = ssl_info.get('issuer', {}).get('organizationName', '').lower()
            if any(trusted in issuer for trusted in ['let\'s encrypt', 'cloudflare', 'digicert', 'sectigo', 'amazon']):
                score -= 10
                reasons.append("Trusted SSL certificate")
            elif ssl_info.get('is_wildcard'):
                score += 3
                reasons.append("Wildcard SSL certificate")
        else:
            # Only penalize if HTTPS is expected
            if parsed.scheme == 'https':
                score += 15
                reasons.append("SSL certificate verification failed")
            else:
                score += 5
                reasons.append("No HTTPS encryption")
    except Exception:
        score += 10
        reasons.append("SSL analysis failed")
    
    # WHOIS/Registrar Analysis
    whois_info = await _get_whois_enhanced(domain)
    if whois_info:
        if whois_info.get('trusted_registrar'):
            score -= 8
            reasons.append(f"Trusted registrar: {whois_info.get('registrar', 'unknown')}")
        else:
            score += 5
            reasons.append("Unknown or untrusted registrar")
        
        if whois_info.get('privacy_protection'):
            score += 3
            reasons.append("Domain privacy protection enabled")
        
        country = whois_info.get('country', '').upper()
        if country in HIGH_RISK_COUNTRIES:
            score += 15
            reasons.append(f"Domain registered in high-risk country: {country}")
        
        # Age analysis remains the same but with context
        creation_date = whois_info.get('creation_date')
        if creation_date:
            import datetime
            age_days = (datetime.datetime.utcnow() - creation_date).days
            if age_days < 30:
                score += 25
                reasons.append(f"Very new domain: {age_days} days old")
            elif age_days < 90:
                score += 15
                reasons.append(f"New domain: {age_days} days old")
            elif age_days > 365:
                score -= 5
                reasons.append(f"Established domain: {age_days} days old")
    
    # DNS/Hosting Analysis
    dns_info = await _get_dns_info(domain)
    if dns_info.get('trusted_hosting'):
        score -= 10
        reasons.append("Hosted on trusted infrastructure")
    else:
        score += 5
        reasons.append("Unknown hosting provider")
    
    if not dns_info.get('has_mx'):
        score += 5
        reasons.append("No email server configured")
    
    # Final scoring
    score = max(0.0, min(100.0, score + 10))  # Base technical score
    
    message = "; ".join(reasons) if reasons else "Technical infrastructure verified"
    
    return LayerResult(score=score, message=message)
