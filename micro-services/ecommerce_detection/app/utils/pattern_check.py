import re
from bs4 import BeautifulSoup
import requests

# Define some suspicious patterns
SUSPICIOUS_PHRASES = [
    "limited stock",
    "act now",
    "buy 1 get 3",
    "too good to be true",
    "90% off",
    "today only",
    "exclusive offer",
    "guaranteed delivery",
    "COD only",
    "no returns",
]

def detect_suspicious_patterns(url: str):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text().lower()

        issues = [phrase for phrase in SUSPICIOUS_PHRASES if phrase in text]
        return {
            "issues": issues,
            "is_suspicious": len(issues) > 0
        }
    except Exception as e:
        return {
            "issues": [f"Pattern check failed: {e}"],
            "is_suspicious": False
        }
