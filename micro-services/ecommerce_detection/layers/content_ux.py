from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List
import re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

FAKE_URGENCY_PHRASES = [
    r"last\s*few\s*left",
    r"only\s*\d+\s*left",
    r"today\s*only",
    r"limited\s*time",
    r"flash\s*sale",
    r"act\s*now",
    r"buy\s*now",
    r"\d+%\s*off",
    r"special\s*offer",
    r"limited\s*stock"
]

# Configuration
PLATFORM_DOMAINS = [
    "amazon.com", "flipkart.com", "myntra.com", "ajio.com", "nykaa.com",
    "meesho.com", "snapdeal.com", "shopclues.com", "paytmmall.com",
    "ebay.com", "alibaba.com", "walmart.com", "target.com", "bestbuy.com"
]

HOSTED_STOREFRONT_SUFFIXES = [
    "myshopify.com", "bigcommerce.com", "squarespace.com", "wix.com",
    "shopify.com", "wordpress.com", "webflow.io"
]

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "rediffmail.com",
    "ymail.com", "aol.com", "mail.com", "protonmail.com", "temp-mail.org"
}

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

@dataclass
class LayerResult:
    score: float
    message: str


async def _fetch_html(url: str) -> str | None:
    """Fetch HTML content from URL."""
    try:
        timeout = httpx.Timeout(3.0, connect=1.5)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            res = await client.get(url)
            if res.status_code < 400 and "text/html" in res.headers.get("content-type", ""):
                return res.text
    except Exception:
        return None
    return None


def _check_policy_presence(soup: BeautifulSoup) -> tuple[int, list[str]]:
    """Check for presence of important policies and contact information."""
    risk = 0
    reasons: list[str] = []
    text = soup.get_text(" ").lower()
    policies = ["refund", "return", "privacy", "terms", "contact"]
    missing = [p for p in policies if p not in text]
    if missing:
        risk += 20
        reasons.append(f"Policies missing: {', '.join(missing[:3])}")
    # contact info
    if not re.search(r"\bcontact\b|\bemail\b|\bphone\b", text):
        risk += 15
        reasons.append("Contact info not obvious")
    return risk, reasons


def _check_fake_urgency(soup: BeautifulSoup) -> tuple[int, list[str]]:
    """Check for fake urgency tactics."""
    risk = 0
    reasons: list[str] = []
    text = soup.get_text(" ").lower()
    for pat in FAKE_URGENCY_PHRASES:
        if re.search(pat, text):
            risk += 10
            reasons.append("Fake urgency detected")
            break
    return risk, reasons


async def analyze(url: str) -> LayerResult:
    """
    Analyze content and UX aspects of the website.
    Returns higher score for risky signals.
    """
    html = await _fetch_html(url)
    if not html:
        return LayerResult(score=20.0, message="Could not fetch page or not HTML")
    
    soup = BeautifulSoup(html, "html.parser")  # Use html.parser instead of lxml
    total_risk = 0
    reasons: list[str] = []

    # Platform-aware: if root domain is a known platform and not a hosted storefront, don't apply policy penalties
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower()
    is_platform_root = any(host.endswith(p) for p in PLATFORM_DOMAINS)
    is_hosted_store = any(host.endswith(suf) for suf in HOSTED_STOREFRONT_SUFFIXES)
    
    if not is_platform_root or is_hosted_store:
        r1, rs1 = _check_policy_presence(soup)
        total_risk += r1
        reasons += rs1

    r2, rs2 = _check_fake_urgency(soup)
    total_risk += r2
    reasons += rs2

    # Heuristic: detect presence of social links (trust signal) vs none
    social = [a.get('href','') for a in soup.find_all('a')]
    if not any(any(s in h for s in ["facebook.com","twitter.com","x.com","instagram.com","linkedin.com"]) for h in social):
        total_risk += 5
        reasons.append("No social presence links detected")

    # Shallow broken link scan (only anchors on same host, up to 5)
    try:
        samples = [a.get('href') for a in soup.find_all('a', href=True)][:10]
        broken = 0
        if samples:
            base = url
            timeout = httpx.Timeout(2.0, connect=1.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                for href in samples[:3]:
                    full = urljoin(base, href)
                    try:
                        r = await client.head(full)
                        if r.status_code >= 400:
                            broken += 1
                    except Exception:
                        broken += 1
        if broken >= 3:
            total_risk += 10
            reasons.append(f"Broken links detected: {broken}")
    except Exception:
        pass

    # Contact email domain heuristic (free email domains for store contact)
    try:
        emails = set(re.findall(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)", soup.get_text(" ")))
        for dom in emails:
            if dom.lower() in FREE_EMAIL_DOMAINS:
                total_risk += 10
                reasons.append(f"Contact email uses free domain: {dom}")
                break
    except Exception:
        pass

    # Brand lookalike heuristic via page title
    try:
        # Apply brand title mismatch only when not on platform root (homepages often reference multiple brands)
        if not is_platform_root or is_hosted_store:
            title = (soup.title.string or "").lower() if soup.title else ""
            for brand, canon_list in CANONICAL_BRANDS.items():
                if brand in title:
                    if not any(c in url for c in canon_list):
                        total_risk += 25
                        reasons.append(f"Brand lookalike: mentions '{brand}' but domain not canonical")
                        break
    except Exception:
        pass

    msg = "; ".join(reasons) if reasons else "Basic policy/contact checks passed"
    return LayerResult(score=min(100.0, float(total_risk)), message=msg)
