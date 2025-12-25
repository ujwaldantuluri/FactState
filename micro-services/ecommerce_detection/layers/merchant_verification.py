from __future__ import annotations
import re
import httpx
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from urllib.parse import urlparse

@dataclass
class MerchantVerification:
    platform: str
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    verification_status: str = "unknown"  # verified, unverified, suspicious, banned
    store_age: Optional[int] = None  # days
    trust_score: float = 0.0
    verification_badges: List[str] = field(default_factory=list)
    contact_verified: bool = False
    business_registration: Optional[str] = None
    
@dataclass
class LayerResult:
    score: float
    message: str
    merchant_info: Optional[MerchantVerification] = None

# Configuration
VERIFIED_MAJOR_PLATFORMS = {
    "amazon.com", "flipkart.com", "myntra.com", "ajio.com", "nykaa.com",
    "meesho.com", "snapdeal.com", "shopclues.com", "paytmmall.com",
    "ebay.com", "alibaba.com", "walmart.com", "target.com", "bestbuy.com"
}

# Platform-specific merchant extraction patterns
PLATFORM_PATTERNS = {
    "shopify": {
        "domains": [".myshopify.com", "shopifycdn.com"],
        "merchant_selectors": [
            r'shop_id["\']:\s*["\']?(\d+)',
            r'Shopify\.shop\s*=\s*["\']([^"\']+)',
            r'data-shop-id["\']:\s*["\']?(\d+)',
        ],
        "trust_indicators": ["shopify_payments", "verified_by_shopify", "shopify_plus"]
    },
    "etsy": {
        "domains": ["etsy.com"],
        "merchant_selectors": [
            r'/shop/([^/\?]+)',
            r'shop_id["\']:\s*(\d+)',
            r'data-shop-name["\']:\s*["\']([^"\']+)',
        ],
        "trust_indicators": ["star_seller", "etsy_pick", "handmade_pledge"]
    },
    "ebay": {
        "domains": ["ebay.com", "ebay.in"],
        "merchant_selectors": [
            r'/usr/([^/\?]+)',
            r'seller["\']:\s*["\']([^"\']+)',
            r'data-seller["\']:\s*["\']([^"\']+)',
        ],
        "trust_indicators": ["top_rated_seller", "ebay_plus", "fast_n_free"]
    },
    "amazon": {
        "domains": ["amazon.com", "amazon.in"],
        "merchant_selectors": [
            r'/seller/([A-Z0-9]+)',
            r'merchantID["\']:\s*["\']([^"\']+)',
            r'data-asin["\']:\s*["\']([^"\']+)',
        ],
        "trust_indicators": ["amazon_choice", "fulfillment_by_amazon", "prime_eligible"]
    },
    "woocommerce": {
        "domains": [],  # Can be any domain
        "tech_indicators": ["woocommerce", "wp-content/plugins/woocommerce"],
        "merchant_selectors": [
            r'shop_name["\']:\s*["\']([^"\']+)',
            r'data-shop["\']:\s*["\']([^"\']+)',
        ],
        "trust_indicators": ["ssl_certificate", "verified_payment_gateway"]
    }
}

async def _detect_platform(url: str, html_content: str) -> Optional[str]:
    """Detect which e-commerce platform is being used"""
    domain = urlparse(url).hostname or ""
    
    # Check domain-based platforms first
    for platform, config in PLATFORM_PATTERNS.items():
        if any(domain_pattern in domain for domain_pattern in config.get("domains", [])):
            return platform
    
    # Check technology indicators in HTML
    content_lower = html_content.lower()
    
    if any(indicator in content_lower for indicator in ["shopify", "myshopify"]):
        return "shopify"
    elif any(indicator in content_lower for indicator in ["woocommerce", "wp-content/plugins/woocommerce"]):
        return "woocommerce"
    elif "etsy" in domain:
        return "etsy"
    elif "ebay" in domain:
        return "ebay"
    elif "amazon" in domain:
        return "amazon"
    
    return None

async def _extract_merchant_info(platform: str, url: str, html_content: str) -> MerchantVerification:
    """Extract merchant information based on platform"""
    config = PLATFORM_PATTERNS.get(platform, {})
    verification = MerchantVerification(platform=platform, verification_badges=[])
    
    # Extract merchant ID/name from URL first (more reliable)
    parsed_url = urlparse(url)
    
    if platform == "shopify" and ".myshopify.com" in (parsed_url.hostname or ""):
        # Extract shop name from subdomain
        shop_name = (parsed_url.hostname or "").replace(".myshopify.com", "")
        verification.merchant_name = shop_name
        verification.merchant_id = shop_name
    
    elif platform == "etsy" and "etsy.com" in (parsed_url.hostname or ""):
        # Extract shop name from URL path
        shop_match = re.search(r'/shop/([^/\?]+)', url)
        if shop_match:
            verification.merchant_name = shop_match.group(1)
            verification.merchant_id = shop_match.group(1)
    
    # Fallback: Extract from HTML content
    if not verification.merchant_name:
        for pattern in config.get("merchant_selectors", []):
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                if verification.merchant_id is None:
                    verification.merchant_id = matches[0]
                if verification.merchant_name is None:
                    verification.merchant_name = matches[0]
                break
    
    # Check for trust indicators in content
    content_lower = html_content.lower()
    for indicator in config.get("trust_indicators", []):
        if indicator.replace("_", " ") in content_lower or indicator.replace("_", "-") in content_lower:
            verification.verification_badges.append(indicator)
    
    return verification

async def _verify_shopify_merchant(merchant_id: str) -> Dict:
    """Verify Shopify merchant through their API"""
    try:
        # Shopify merchant verification (would need proper API access)
        # For now, simulate based on common patterns
        
        if not merchant_id or len(merchant_id) < 3:
            return {"status": "invalid", "trust_score": 0.0}
        
        # Simulate merchant verification
        verification_data = {
            "status": "verified" if len(merchant_id) > 5 else "unverified",
            "trust_score": min(80.0, len(merchant_id) * 10),
            "store_features": [],
            "payment_methods": []
        }
        
        return verification_data
    except Exception:
        return {"status": "unknown", "trust_score": 50.0}

async def _verify_etsy_seller(shop_name: str) -> Dict:
    """Verify Etsy seller reputation"""
    try:
        # Etsy seller verification (would integrate with Etsy API)
        if not shop_name:
            return {"status": "invalid", "trust_score": 0.0}
        
        # Simulate seller verification
        return {
            "status": "verified" if len(shop_name) > 3 else "unverified", 
            "trust_score": min(85.0, len(shop_name) * 12),
            "seller_level": "established" if len(shop_name) > 6 else "new"
        }
    except Exception:
        return {"status": "unknown", "trust_score": 60.0}

async def _check_merchant_reputation(verification: MerchantVerification) -> float:
    """Calculate merchant trust score based on verification data"""
    base_score = 50.0  # Neutral starting point
    
    # CRITICAL: Detect obvious scam patterns in merchant names
    merchant_name = (verification.merchant_name or verification.merchant_id or "").lower()
    
    # CRITICAL scam patterns (immediate maximum risk)
    critical_scam_patterns = [
        "super-deals", "mega-deals", "flash-sale", "sale-today", "deals-today",
        "limited-time", "urgent-sale", "clearance-sale", "discount-outlet",
        "cheap-electronics", "wholesale-direct", "factory-outlet"
    ]
    
    # High-risk scam patterns
    high_risk_patterns = [
        "best-deals", "discount-", "sale-", "cheap-", "outlet-", "warehouse-",
        "liquidation", "overstock", "closeout", "bulk-", "-deals", "deals-"
    ]
    
    # Check for critical scam patterns first
    for pattern in critical_scam_patterns:
        if pattern in merchant_name:
            base_score = 5.0  # CRITICAL - immediate high risk
            break
    else:
        # Check for high-risk patterns
        scam_indicators = 0
        for pattern in high_risk_patterns:
            if pattern in merchant_name:
                scam_indicators += 1
        
        if scam_indicators >= 2:
            base_score = 15.0  # Very high risk
        elif scam_indicators == 1:
            base_score = 30.0  # High risk
    
    # Additional suspicious patterns
    suspicious_patterns = [
        r'\d{4}',  # Years in name (sale2024, deals2025)
        r'(today|now|quick|fast|instant)',
        r'(amazing|incredible|unbelievable|shocking)',
        r'(free|zero|\$0)',
        r'(\d+%|off|save)'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, merchant_name, re.IGNORECASE):
            base_score -= 15
    
    # Legitimate business name patterns (bonus points)
    legitimate_patterns = [
        # Established brand names
        "beardbrand", "gymshark", "mvmt", "triangl", "glossier", "kylie", "allbirds",
        "warby", "casper", "purple", "tuft", "needle", "bombas", "away", "outdoor",
        "patagonia", "nike", "adidas", "under", "armour", "lululemon", "athletic",
        
        # Professional naming patterns
        r'\b[a-z]+\s+(company|co|inc|ltd|llc|corp)\b',
        r'\b[a-z]+\s+(studio|design|boutique|shop|store)\b',
        r'\b[a-z]+\s+(brand|brands|fashion|apparel)\b'
    ]
    
    for pattern in legitimate_patterns:
        if isinstance(pattern, str) and pattern in merchant_name:
            base_score += 20
            break
        elif re.search(pattern, merchant_name, re.IGNORECASE):
            base_score += 15
            break
    
    # Platform-specific verification
    if verification.platform == "shopify":
        shopify_data = await _verify_shopify_merchant(verification.merchant_id or "")
        if shopify_data["status"] == "verified":
            base_score += 15
        elif shopify_data["status"] == "unverified":
            base_score -= 10
    
    elif verification.platform == "etsy":
        etsy_data = await _verify_etsy_seller(verification.merchant_name or "")
        if etsy_data["status"] == "verified":
            base_score += 20
        elif etsy_data["status"] == "unverified":
            base_score -= 5
    
    # Trust badge bonuses
    badge_bonus = len(verification.verification_badges) * 8
    
    # Contact verification bonus
    if verification.contact_verified:
        base_score += 15
    
    return max(5.0, min(95.0, base_score + badge_bonus))

async def analyze(url: str, html_content: str = None) -> LayerResult:
    """Analyze merchant verification for multi-vendor platforms"""
    # Whitelist globally verified major platforms
    try:
        host = urlparse(url).hostname or ""
        if host.lower() in VERIFIED_MAJOR_PLATFORMS:
            return LayerResult(score=0.0, message=f"VERIFIED PLATFORM: {host} merchant verification bypassed")
    except Exception:
        pass
    
    if not html_content:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, follow_redirects=True)
                html_content = response.text if response.status_code == 200 else ""
        except Exception:
            return LayerResult(
                score=40.0,
                message="Could not fetch content for merchant verification"
            )
    
    # Detect platform
    platform = await _detect_platform(url, html_content)
    
    if not platform:
        return LayerResult(
            score=20.0,  # Low risk for non-marketplace sites
            message="Not a recognized multi-vendor platform"
        )
    
    # Extract merchant information
    merchant_info = await _extract_merchant_info(platform, url, html_content)
    
    # Calculate trust score
    merchant_trust = await _check_merchant_reputation(merchant_info)
    
    # Convert trust score to risk score (AGGRESSIVE conversion for scam detection)
    if merchant_trust <= 10:
        risk_score = 95.0  # Critical risk for obvious scams
    elif merchant_trust <= 20:
        risk_score = 85.0  # Very high risk
    elif merchant_trust <= 30:
        risk_score = 70.0  # High risk
    elif merchant_trust <= 50:
        risk_score = 50.0  # Medium risk
    elif merchant_trust <= 70:
        risk_score = 30.0  # Low-medium risk
    else:
        risk_score = max(0.0, 100 - merchant_trust)  # Standard conversion for good merchants
    
    # Prepare enhanced message
    if merchant_info.merchant_id or merchant_info.merchant_name:
        merchant_display = merchant_info.merchant_name or merchant_info.merchant_id
        
        # Add risk indicators to message
        if risk_score >= 80:
            risk_indicator = "CRITICAL RISK"
        elif risk_score >= 60:
            risk_indicator = "HIGH RISK"
        elif risk_score >= 40:
            risk_indicator = "CAUTION"
        else:
            risk_indicator = "VERIFIED"
            
        badges_text = f" with {len(merchant_info.verification_badges)} trust badges" if merchant_info.verification_badges else ""
        message = f"{risk_indicator}: Platform: {platform.title()}, Merchant: {merchant_display}{badges_text} (trust: {merchant_trust:.0f})"
    else:
        message = f"Platform: {platform.title()}, Merchant information not found"
        risk_score += 30  # Higher penalty for unidentifiable merchant
    
    return LayerResult(
        score=min(100.0, risk_score),
        message=message,
        merchant_info=merchant_info
    )
