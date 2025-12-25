from __future__ import annotations
from dataclasses import dataclass
import httpx
import os

@dataclass
class LayerResult:
    score: float
    message: str

async def _safe_browsing_check(url: str, api_key: str) -> tuple[float, str]:
    """Check URL against Google Safe Browsing API."""
    if not api_key:
        return 0.0, "SafeBrowsing not configured"
    try:
        endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        payload = {
            "client": {"clientId": "fake-ecom-detector", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(6.0, connect=3.0)) as client:
            res = await client.post(f"{endpoint}?key={api_key}", json=payload)
            if res.status_code >= 400:
                return 0.0, f"SafeBrowsing error {res.status_code}"
            data = res.json()
            if data.get("matches"):
                return 60.0, "SafeBrowsing match found"
            return 0.0, "SafeBrowsing: no matches"
    except Exception as e:
        return 0.0, f"SafeBrowsing check failed: {str(e)}"

async def analyze(url: str) -> LayerResult:
    """
    Analyze URL using external threat intelligence sources.
    Checks against SafeBrowsing and other threat databases.
    """
    # Get API keys from environment
    safe_browsing_api_key = os.getenv("SAFE_BROWSING_API_KEY")
    phishtank_api_key = os.getenv("PHISHTANK_API_KEY")
    
    apis = []
    if safe_browsing_api_key:
        apis.append("SafeBrowsing")
    if phishtank_api_key:
        apis.append("PhishTank")

    notes: list[str] = []
    total_risk = 0.0
    
    if safe_browsing_api_key:
        s, m = await _safe_browsing_check(url, safe_browsing_api_key)
        total_risk += s
        notes.append(m)
    
    if phishtank_api_key:
        # PhishTank implementation could be added here
        notes.append("PhishTank configured (not implemented)")

    if notes:
        return LayerResult(score=min(100.0, total_risk), message="; ".join(notes))
    return LayerResult(score=10.0, message="No external threat intel configured")
