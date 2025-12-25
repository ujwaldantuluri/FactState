from __future__ import annotations
from urllib.parse import urlparse
from ..config import settings

def _is_verified_host(host: str) -> bool:
    h = (host or "").lower()
    if h in settings.verified_major_platforms:
        return True
    if h.startswith("www.") and h[4:] in settings.verified_major_platforms:
        return True
    return False

PHISHING_TOKENS = {
    "refund", "order", "support", "help", "verify", "verification",
    "payment", "pay", "secure", "security", "account", "update", "login",
    "billing", "wallet", "upi", "reset", "unlock"
}

BADGE_ORDER = ["Verified Safe", "Low Risk", "Caution", "High Risk", "Critical"]


def _host_tokens(host: str) -> set[str]:
    parts = host.split(".")
    if len(parts) >= 2:
        parts = parts[:-1]
    tokens: set[str] = set()
    for p in parts:
        for t in p.replace("-", " ").split():
            if t:
                tokens.add(t.lower())
    return tokens


def apply_safety_gates(url: str, reasons: list[dict], raw_score: float) -> tuple[float, str]:
    """
    Post-process raw score with conservative gates:
    - Phishing tokens in subdomain -> +25 and at least Caution
    - Any core layer failure/timeout -> at least Caution; if >=3 failures, +20
    - Typosquatting/critical wording -> floor to High Risk
    - Verified Safe allowed only when no failures and score < 15
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    tokens = _host_tokens(host)

    min_badge = "Verified Safe"
    score = float(raw_score)
    failures = 0
    text = " ".join([str(r.get("message", "")) for r in reasons]).lower()

    failure_markers = (
        "timed out", "could not fetch", "failed", "not html", "no ssl", "certificate verification failed",
    )
    for r in reasons:
        msg = str(r.get("message", "")).lower()
        layer = r.get("layer", "")
        # Skip counting merchant_verification failures for verified major platforms (host or www.host)
        if _is_verified_host(host) and layer == "merchant_verification":
            continue
        if any(m in msg for m in failure_markers):
            failures += 1

    # Major platform trust: allow one benign failure without forcing Caution
    if failures >= 1:
        if _is_verified_host(host) and failures == 1:
            pass
        else:
            min_badge = "Caution"
    if failures >= 3:
        score += 20
        min_badge = "Caution"

    if any(tok in tokens for tok in PHISHING_TOKENS):
        # Do NOT penalize if it's a verified major platform main domain (host or www.host)
        if not _is_verified_host(host):
            score += 25
            min_badge = "Caution"

    if ("typosquatting" in text) or ("critical threat" in text) or ("homograph" in text):
        score = max(score, 70.0)
        min_badge = "High Risk"

    score = max(0.0, min(100.0, score))

    if failures == 0 and score < 18:
        final_badge = "Verified Safe"
    else:
        if score < 25:
            badge = "Low Risk"
        elif score < 45:
            badge = "Caution"
        elif score < 70:
            badge = "High Risk"
        else:
            badge = "Critical"

        # Enforce minimum severity
        if BADGE_ORDER.index(badge) < BADGE_ORDER.index(min_badge):
            final_badge = min_badge
        else:
            final_badge = badge

    return score, final_badge
