
import whois
from datetime import datetime
import ssl

import asyncio
import httpx
from fastapi.concurrency import run_in_threadpool

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
import imagehash
from io import BytesIO
import os

import asyncio

import httpx
from fastapi.concurrency import run_in_threadpool

# --- Domain Age (Using Thread Pool for synchronous `whois`) ---
async def check_domain_age(domain):
    def _check():
        print("in check_domain_age")
        domain_info = whois.whois(domain)
        creation_date = domain_info.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if not creation_date:
            return {"error": "Creation date not found", "domain": domain, "is_suspicious": True}
        age_days = (datetime.now() - creation_date).days
        print("out check_domain_age")
        return {"domain": domain, "creation_date": creation_date.strftime("%Y-%m-%d"), "age_days": age_days, "is_suspicious": age_days < 180}
    try:
        return await run_in_threadpool(_check)
    except Exception as e:
        return {"error": str(e), "domain": domain, "is_suspicious": True}

# --- WHOIS Analysis (Using Thread Pool) ---
async def analyze_whois(domain):
    def _analyze():
        print("in analyze_whois")
        data = whois.whois(domain)
        registrar = data.registrar or "Unknown"
        suspicious_registrar = any(r in registrar.lower() for r in ["privacy", "guard", "whois", "protected", "cheap", "fastdomain"])
        print("out analyze_whois")

        return {"registrar": registrar, "country": data.country or "Unknown", "email": data.emails[0] if isinstance(data.emails, list) and data.emails else None, "suspicious": suspicious_registrar}
    try:
        return await run_in_threadpool(_analyze)
    except Exception as e:
        return {"registrar": None, "country": None, "email": None, "suspicious": True, "error": str(e)}

# --- SSL Certificate (Using asyncio streams for native async) ---
async def check_ssl_certificate(domain):
    try:
        print("in check_ssl_certificate")

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(domain, 443, ssl=ssl.create_default_context()), timeout=5
        )
        cert = writer.get_extra_info('peercert')
        writer.close()
        await writer.wait_closed()
        
        valid_to = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
        print("out check_ssl_certificate")
        return {"issuer": cert.get('issuer', []), "subject": cert.get('subject', []), "is_valid": datetime.utcnow() < valid_to, "suspicious": datetime.utcnow() >= valid_to}
    except Exception as e:
        return {"is_valid": False, "suspicious": True, "error": str(e)}

# --- Headers Analysis (Async with httpx) ---
async def analyze_headers(url, client: httpx.AsyncClient):
    try:
        print("in analyze_headers")
        resp = await client.get(url, timeout=5, follow_redirects=True)
        headers = resp.headers
        issues = []
        if "php/5" in headers.get("X-Powered-By", "").lower(): issues.append("Outdated PHP version")
        if "apache/2.2" in headers.get("Server", "").lower(): issues.append("Old Apache version")
        print("out analyze_headers")
        return {"server": headers.get("Server", "Unknown"), "x_powered_by": headers.get("X-Powered-By", "Unknown"), "issues": issues, "suspicious": len(issues) > 0}
    except Exception as e:
        return {"issues": [], "suspicious": False, "error": str(e)}

# --- Suspicious Patterns (Async with httpx) ---
async def detect_suspicious_patterns(url, client: httpx.AsyncClient):
    SUSPICIOUS_PHRASES = ["limited stock", "act now", "buy 1 get 3", "90% off", "today only"]
    try:
        print("in detect_suspicious_patterns")
        response = await client.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text().lower()
        issues = [phrase for phrase in SUSPICIOUS_PHRASES if phrase in text]
        print("out detect_suspicious_patterns")
        return {"issues": issues, "is_suspicious": len(issues) > 0}
    except Exception as e:
        return {"issues": [], "is_suspicious": False, "error": str(e)}

# --- Google Safe Browse (Async with httpx) ---
async def check_safe_Browse(url, client: httpx.AsyncClient):
    api_key = os.getenv("GOOGLE_SAFE_Browse_API_KEY")
    if not api_key: return {"safe": False, "checked": False, "suspicious": True, "error": "API key missing"}
    
    api_url = f"https://safeBrowse.googleapis.com/v4/threatMatches:find?key={api_key}"
    body = {"client": {"clientId": "your-client-id", "clientVersion": "1.0"}, "threatInfo": {"threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"], "platformTypes": ["ANY_PLATFORM"], "threatEntryTypes": ["URL"], "threatEntries": [{"url": url}]}}
    
    try:
        print("in check_safe_Browse")
        res = await client.post(api_url, json=body, timeout=5)
        data = res.json()
        is_safe = not data.get("matches")
        print("out check_safe_Browse")
        return {"safe": is_safe, "checked": True, "suspicious": not is_safe}
    except Exception as e:
        return {"safe": False, "checked": False, "suspicious": True, "error": str(e)}

# --- Broken Links (Fully Concurrent) ---
async def check_broken_links(url, client: httpx.AsyncClient):
    try:
        print("in check_broken_links")
        response = await client.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        links = [urljoin(url, tag['href']) for tag in soup.find_all("a", href=True)]
        
        async def check_one(link):
            try:
                # Use HEAD request for efficiency
                res = await client.head(link, timeout=3, follow_redirects=True)
                return res.status_code >= 400
            except (httpx.RequestError, asyncio.TimeoutError):
                return True # Count as broken on error/timeout

        check_tasks = [check_one(link) for link in links]
        results = await asyncio.gather(*check_tasks)
        
        broken_count = sum(results)
        total_count = len(links)
        suspicious = total_count > 5 and (broken_count / total_count) > 0.2
        print("out check_broken_links")
        return {"total_links": total_count, "broken_links": broken_count, "suspicious": suspicious}
    except Exception as e:
        return {"total_links": 0, "broken_links": 0, "suspicious": False, "error": str(e)}

# --- Logo Similarity (Complex: Async I/O + Sync CPU-bound) ---
BRAND_LOGOS = {} # Populate this as before

async def check_logo_similarity(website_url, client: httpx.AsyncClient):
    # 1. Async part: Fetching URLs and image data
    try:
        resp = await client.get(website_url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        icon_link = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        logo_url = urljoin(website_url, icon_link["href"]) if icon_link and icon_link.get("href") else None
        
        if not logo_url:
            return {"logo_found": False, "suspicious": False, "reason": "Logo not found"}

        img_response = await client.get(logo_url, timeout=5)
        img_bytes = img_response.content
    except Exception as e:
        return {"logo_found": False, "suspicious": False, "error": f"Logo fetch failed: {e}"}

    # 2. Sync part: Image processing (CPU-bound)
    def _process_image():
        logo_image = Image.open(BytesIO(img_bytes)).convert("RGB")
        test_hash = imagehash.average_hash(logo_image)
        for brand, known_hash in BRAND_LOGOS.items():
            diff = test_hash - known_hash
            if diff < 10:
                return {"logo_found": True, "suspicious": True, "matched_brand": brand, "hash_difference": diff}
        return {"logo_found": True, "suspicious": False}

    try:
        # Run the CPU-bound part in the thread pool
        result = await run_in_threadpool(_process_image)
        result["logo_url"] = logo_url
        return result
    except Exception as e:
        return {"logo_found": False, "suspicious": False, "error": f"Logo processing failed: {e}"}






