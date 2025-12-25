import requests

def analyze_headers(url):
    try:
        resp = requests.get(url, timeout=5)
        headers = resp.headers

        server = headers.get("Server", "Unknown")
        x_powered_by = headers.get("X-Powered-By", "Unknown")

        issues = []
        if "php/5" in x_powered_by.lower():
            issues.append("Outdated PHP version")
        if "apache/2.2" in server.lower():
            issues.append("Old Apache version")

        return {
            "server": server,
            "x_powered_by": x_powered_by,
            "issues": issues,
            "suspicious": len(issues) > 0
        }

    except Exception as e:
        return {
            "server": None,
            "x_powered_by": None,
            "issues": [],
            "suspicious": False,
            "error": str(e)
        }
