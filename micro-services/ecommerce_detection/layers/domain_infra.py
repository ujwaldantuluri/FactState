from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
import datetime as dt
from urllib.parse import urlparse
from difflib import SequenceMatcher

try:
    import idna
    IDNA_AVAILABLE = True
except ImportError:
    IDNA_AVAILABLE = False

try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False

@dataclass
class LayerResult:
    score: float  # 0..100 higher = riskier
    message: str

# Configuration constants
VERIFIED_MAJOR_PLATFORMS = {
    "amazon.com", "flipkart.com", "myntra.com", "ajio.com", "nykaa.com",
    "meesho.com", "snapdeal.com", "shopclues.com", "paytmmall.com",
    "ebay.com", "alibaba.com", "walmart.com", "target.com", "bestbuy.com"
}

SUSPICIOUS_TLDS = {
    ".tk", ".ml", ".ga", ".cf", ".top", ".click", ".download", ".stream",
    ".science", ".racing", ".cricket", ".party", ".review", ".faith",
    ".accountant", ".loan", ".men", ".bid", ".trade", ".win"
}

HOSTED_STOREFRONT_SUFFIXES = [
    "myshopify.com", "bigcommerce.com", "squarespace.com", "wix.com",
    "shopify.com", "wordpress.com", "webflow.io"
]

CANONICAL_BRANDS = {
    "amazon": ["amazon.com", "amazon.in", "amazon.co.uk"],
    "flipkart": ["flipkart.com"],
    "google": ["google.com", "google.co.in"],
    "facebook": ["facebook.com", "meta.com"],
    "paypal": ["paypal.com"],
    "apple": ["apple.com"],
    "microsoft": ["microsoft.com"],
    "myntra": ["myntra.com"],
    "nykaa": ["nykaa.com"]
}

PHISHING_TOKENS = {
    "refund", "order", "support", "verify", "payment", "account", "login", 
    "secure", "security", "update", "billing", "wallet", "upi", "reset", "unlock"
}


def _domain_age_days(domain: str) -> Optional[int]:
    """Get domain age in days using whois."""
    if not WHOIS_AVAILABLE or not domain:
        return None
    try:
        data = whois.whois(domain)
        created = data.creation_date
        if isinstance(created, list):
            created = created[0]
        if not created:
            return None
        if isinstance(created, dt.datetime):
            created_dt = created
        else:
            return None
        return (dt.datetime.utcnow() - created_dt).days
    except Exception:
        return None


def _detect_typosquatting(domain: str) -> float:
    """Advanced typosquatting detection with multiple strategies."""
    if not domain:
        return 0.0
    
    risk = 0.0
    parts = domain.split('.')
    sld = parts[-2] if len(parts) >= 2 else parts[0]
    
    # Known typosquatting patterns for major brands
    typosquat_patterns = {
        "amazon": ["amzon", "amazom", "amazone", "amazn", "amaozn", "amaxon", "amzaon"],
        "flipkart": ["flipkrt", "flipkat", "flikart", "flpkart", "flipcart"],
        "google": ["googel", "gogle", "googl", "goolge", "gooogle"],
        "facebook": ["facbook", "facebuk", "facboook", "facebok"],
        "paypal": ["payp4l", "payapl", "paipal", "paypal1"],
        "apple": ["aple", "appel", "aplle", "applle"],
        "microsoft": ["mircosoft", "microsooft", "micorsoft"],
    }
    
    # Check exact matches against known typosquats
    for brand, patterns in typosquat_patterns.items():
        if sld.lower() in patterns:
            return 85.0  # Critical risk for known typosquats
    
    # Advanced character-level analysis
    for brand, canon_list in CANONICAL_BRANDS.items():
        # Skip if already canonical
        if any(c in domain for c in canon_list):
            continue
            
        brand_lower = brand.lower()
        sld_lower = sld.lower()
        
        # Character substitution detection
        if len(sld_lower) == len(brand_lower):
            diff_count = sum(1 for a, b in zip(sld_lower, brand_lower) if a != b)
            if diff_count == 1:  # Single character difference
                return 80.0  # Very high risk
            elif diff_count == 2:  # Two character difference  
                return 70.0  # High risk
        
        # Character omission/insertion detection
        elif abs(len(sld_lower) - len(brand_lower)) <= 2:
            sim = SequenceMatcher(None, sld_lower, brand_lower).ratio()
            if sim >= 0.85:  # Very similar despite length difference
                return 75.0  # Very high risk
    
    return risk


def analyze(url: str) -> LayerResult:
    """
    Heuristic domain/infra checks: WHOIS age, SSL presence (scheme), basic sanity.
    Returns higher score for risky signals.
    """
    parsed = urlparse(url)
    domain = parsed.hostname or ""

    reasons = []
    risk = 0.0

    # MAJOR PLATFORM DETECTION - Give huge trust bonus
    if domain.lower() in VERIFIED_MAJOR_PLATFORMS:
        risk = 0.0  # Reset risk to 0 for verified platforms
        reasons.append(f"VERIFIED MAJOR PLATFORM: {domain} is a trusted global platform")
        return LayerResult(score=0.0, message="; ".join(reasons))

    # CRITICAL PRE-FILTER: Known typosquatting patterns
    typosquat_risk = _detect_typosquatting(domain)
    if typosquat_risk > 0:
        risk += typosquat_risk
        if typosquat_risk >= 75:
            reasons.append("CRITICAL THREAT: Known typosquatting pattern detected")
        elif typosquat_risk >= 50:
            reasons.append("HIGH THREAT: Suspicious brand impersonation pattern")

    # SSL scheme
    if parsed.scheme != "https":
        risk += 20
        reasons.append("No HTTPS detected")

    # Domain age
    age_days = _domain_age_days(domain)
    if age_days is None:
        # Unknown age -> slight risk
        risk += 10
        reasons.append("Unknown domain age")
    else:
        if age_days < 30:
            risk += 40
            reasons.append(f"Domain age {age_days} days (<30)")
        elif age_days < 180:
            risk += 20
            reasons.append(f"Domain age {age_days} days (<180)")

    # TLD risk
    try:
        tld = "." + (domain.split(".")[-1] if "." in domain else "")
        if tld and tld.lower() in SUSPICIOUS_TLDS:
            risk += 10
            reasons.append(f"Suspicious TLD {tld}")
    except Exception:
        pass

    # Punycode / IDN homograph suspicion
    try:
        if IDNA_AVAILABLE:
            if domain.startswith("xn--"):
                risk += 10
                reasons.append("IDN/punycode domain")
            else:
                _ = idna.encode(domain)
    except Exception:
        if IDNA_AVAILABLE:
            risk += 5
            reasons.append("Invalid IDNA domain encoding")

    # Excessive subdomains can be phishing signal (e.g., brand.payment.example.xyz)
    if domain.count('.') >= 3:
        risk += 10
        reasons.append("Many subdomains")

    # Brand lookalike vs canonical domains (e.g., amzon vs amazon)
    try:
        parts = domain.split('.')
        sld = parts[-2] if len(parts) >= 2 else parts[0]
        # Skip lookalike on hosted storefronts (*.myshopify.com, etc.)
        if not any(domain.endswith(suf) for suf in HOSTED_STOREFRONT_SUFFIXES):
            for brand, canon_list in CANONICAL_BRANDS.items():
                # Skip if domain already a canonical
                if any(c in domain for c in canon_list):
                    continue
                sim = SequenceMatcher(None, sld.lower(), brand.lower()).ratio()
                
                # CRITICAL: Typosquatting detection with graduated penalties
                if sim >= 0.9:
                    # Very close match - likely typosquatting (e.g., amazom, amzon)
                    risk += 65
                    reasons.append(f"CRITICAL: Typosquatting attack detected: '{sld}' mimics '{brand}' (similarity: {sim:.2f})")
                    break
                elif sim >= 0.82:
                    # Close match - suspicious domain
                    risk += 45
                    reasons.append(f"HIGH RISK: Brand lookalike domain: '{sld}' ~ '{brand}' (similarity: {sim:.2f})")
                    break
                elif sim >= 0.75:
                    # Moderate similarity - potential confusion
                    risk += 25
                    reasons.append(f"SUSPICIOUS: Similar to known brand: '{sld}' ~ '{brand}' (similarity: {sim:.2f})")
                    break
    except Exception:
        pass

    # Hyphen/digit/length heuristics on SLD
    try:
        sld = domain.split('.')[-2] if '.' in domain else domain
        hyphens = sld.count('-')
        digits = sum(ch.isdigit() for ch in sld)
        if hyphens >= 2:
            risk += 10
            reasons.append("Many hyphens in domain")
        if digits >= 3:
            risk += 10
            reasons.append("Many digits in domain")
        if len(sld) >= 20:
            risk += 5
            reasons.append("Very long domain name")
    except Exception:
        pass

    # Subdomain phishing-intent tokens (e.g., order-refund-now.*)
    try:
        host_parts = (parsed.hostname or "").lower().split(".")
        sub_parts = host_parts[:-2] if len(host_parts) > 2 else host_parts[:-1]
        subdomain = ".".join(sub_parts)
        if subdomain:
            toks = {t for p in subdomain.split(".") for t in p.replace("-", " ").split()}
            if any(t in PHISHING_TOKENS for t in toks):
                risk += 25.0
                reasons.append(f"Suspicious intent in subdomain: {subdomain}")
    except Exception:
        pass

    message = "; ".join(reasons) if reasons else "No major domain/infra red flags"
    return LayerResult(score=min(100.0, risk), message=message)
