from __future__ import annotations
import re
import httpx
from dataclasses import dataclass
from typing import Optional, Dict, List
from ...config import settings

@dataclass
class BusinessVerification:
    is_registered: bool
    registration_details: Optional[Dict] = None
    gst_valid: bool = False
    linkedin_verified: bool = False
    phone_verified: bool = False
    address_verified: bool = False
    
@dataclass
class LayerResult:
    score: float
    message: str
    verification: Optional[BusinessVerification] = None

async def _verify_gst_number(gst: str) -> bool:
    """Basic GST number format validation (India)"""
    if not gst or len(gst) != 15:
        return False
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    return bool(re.match(pattern, gst.upper()))

async def _extract_business_info(html: str) -> Dict:
    """Extract business indicators from HTML content"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    text = soup.get_text(' ').lower()
    
    info = {
        'has_gst': bool(re.search(r'\b[0-9]{2}[a-z]{5}[0-9]{4}[a-z]{1}[1-9a-z]{1}z[0-9a-z]{1}\b', text, re.I)),
        'has_phone': bool(re.search(r'\+?[\d\s\-\(\)]{8,15}', text)),
        'has_email': bool(re.search(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', text)),
        'has_address': bool(re.search(r'\b(street|road|avenue|block|plot|building|floor)\b', text)),
        'payment_gateways': [],
        'social_links': [],
        'trust_badges': []
    }
    
    # Detect payment gateways
    for gateway in settings.trusted_payment_processors:
        if gateway.lower() in text:
            info['payment_gateways'].append(gateway)
    
    # Detect social media links
    links = [a.get('href', '') for a in soup.find_all('a', href=True)]
    for link in links:
        if any(social in link for social in ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com']):
            info['social_links'].append(link)
    
    # Detect trust badges/certifications
    if any(badge in text for badge in ['ssl', 'secure', 'verified', 'certified', 'licensed']):
        info['trust_badges'] = ['security_indicators']
    
    return info

async def _verify_opencorporates(company_name: str, country: str = "in") -> Optional[Dict]:
    """Verify company registration via OpenCorporates API"""
    if not settings.opencorporates_api_key:
        return None
    
    try:
        url = f"https://api.opencorporates.com/v0.4/companies/search"
        params = {
            'q': company_name,
            'jurisdiction_code': country,
            'api_token': settings.opencorporates_api_key
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                companies = data.get('results', {}).get('companies', [])
                if companies:
                    return companies[0].get('company', {})
    except Exception:
        pass
    
    return None

async def analyze(url: str, html_content: str = None) -> LayerResult:
    """Comprehensive business verification analysis"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.hostname or ""
    
    # MAJOR PLATFORM BYPASS - Verified platforms are legitimate businesses
    if domain.lower() in settings.verified_major_platforms:
        verification = BusinessVerification(
            is_registered=True,
            registration_details={"status": "Global verified platform"},
            gst_valid=True,  # Major platforms have all compliance
            linkedin_verified=True,
            phone_verified=True,
            address_verified=True
        )
        return LayerResult(
            score=0.0,
            message=f"VERIFIED BUSINESS: {domain} is a globally recognized legitimate business",
            verification=verification
        )
    
    if not html_content:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                html_content = response.text if response.status_code == 200 else ""
        except Exception:
            return LayerResult(
                score=30.0, 
                message="Could not fetch content for business verification"
            )
    
    # Extract business information
    business_info = await _extract_business_info(html_content)
    
    # Score calculation
    score = 0.0
    reasons = []
    
    # Business registration verification
    verification = BusinessVerification(is_registered=False)
    
    # GST verification (India specific)
    if business_info['has_gst']:
        gst_numbers = re.findall(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', 
                                html_content, re.I)
        if gst_numbers:
            gst_valid = await _verify_gst_number(gst_numbers[0])
            verification.gst_valid = gst_valid
            if gst_valid:
                score -= 15  # Reduce risk for valid GST
                reasons.append("Valid GST number found")
            else:
                score += 10  # Increase risk for invalid GST
                reasons.append("Invalid GST number format")
    else:
        score += 5
        reasons.append("No GST/tax number found")
    
    # Contact verification
    contact_score = 0
    if business_info['has_phone']:
        verification.phone_verified = True
        contact_score -= 5
    else:
        contact_score += 10
        reasons.append("No phone number found")
    
    if business_info['has_email']:
        contact_score -= 3
    else:
        contact_score += 8
        reasons.append("No email contact found")
    
    if business_info['has_address']:
        verification.address_verified = True
        contact_score -= 5
    else:
        contact_score += 10
        reasons.append("No physical address found")
    
    score += contact_score
    
    # Payment gateway verification
    if business_info['payment_gateways']:
        score -= 10  # Trusted payment gateways reduce risk
        reasons.append(f"Trusted payment gateways: {', '.join(business_info['payment_gateways'][:2])}")
    else:
        score += 15
        reasons.append("No recognized payment gateways found")
    
    # Social media presence
    if business_info['social_links']:
        verification.linkedin_verified = 'linkedin.com' in str(business_info['social_links'])
        score -= 5
        reasons.append("Social media presence verified")
    else:
        score += 8
        reasons.append("No social media presence")
    
    # Trust indicators
    if business_info['trust_badges']:
        score -= 5
        reasons.append("Security/trust indicators found")
    
    # Final scoring
    score = max(0.0, min(100.0, score + 20))  # Base score of 20 for unknowns
    
    message = "; ".join(reasons) if reasons else "Business verification completed"
    
    return LayerResult(
        score=score,
        message=message,
        verification=verification
    )