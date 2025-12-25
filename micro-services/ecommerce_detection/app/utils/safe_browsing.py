import os
import requests

def check_safe_browsing(url):
    api_key = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")
    if not api_key:
        return {"safe": False, "checked": False, "error": "API key missing"}

    safe_browsing_api = "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=" + api_key
    body = {
        "client": {
            "clientId": "your-client-id",
            "clientVersion": "1.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }

    try:
        res = requests.post(safe_browsing_api, json=body)
        data = res.json()
        if data.get("matches"):
            return {"safe": False, "checked": True}
        else:
            return {"safe": True, "checked": True}
    except Exception as e:
        return {"safe": False, "checked": False, "error": str(e)}
