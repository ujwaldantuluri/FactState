from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import asyncio
from datetime import datetime

# Import analysis layers
from .layers import domain_infra
from .layers import content_ux
from .layers import visual_brand
from .layers import threat_intel
from .layers import user_feedback
from .layers import business_verification
from .layers import technical_verification
from .layers import merchant_verification
from .risk_rules import apply_safety_gates

@dataclass
class Reason:
    layer: str
    message: str
    weight: float
    score: float

# Default weights for scoring layers
DEFAULT_WEIGHTS = {
    "domain_infra": 0.25,
    "content_ux": 0.10,
    "business_verification": 0.15,
    "technical_verification": 0.08,
    "merchant_verification": 0.30,
    "visual_brand": 0.05,
    "threat_intel": 0.12,
    "user_feedback": 0.05,
}

BADGE_THRESHOLDS = {
    "trusted": (0, 25),
    "low_risk": (25, 45),
    "caution": (45, 70),
    "high": (70, 85),
    "critical": (85, 100),
}


def to_badge(score: float) -> str:
    """Convert risk score to human-readable badge."""
    if score < BADGE_THRESHOLDS["trusted"][1]:
        return "✅ Verified Safe"
    elif score < BADGE_THRESHOLDS["low_risk"][1]:
        return "🟢 Low Risk"
    elif score < BADGE_THRESHOLDS["caution"][1]:
        return "⚠️ Caution Required"
    elif score < BADGE_THRESHOLDS["high"][1]:
        return "🔴 High Risk"
    else:
        return "⛔ Critical Risk"


def advice_for(score: float) -> tuple[str, list[str]]:
    """Generate advice based on risk score."""
    if score < 25:
        return ("Safe to proceed", [
            "Business appears legitimate and verified",
            "Merchant verification passed (if applicable)",
            "Use any payment method you're comfortable with",
            "Keep order confirmations for your records"
        ])
    elif score < 45:
        return ("Generally safe with minor concerns", [
            "Business appears legitimate but has some unverified aspects",
            "Check merchant reputation on marketplace platforms",
            "Prefer secure payment methods (credit card, PayPal)",
            "Verify contact details before large purchases"
        ])
    elif score < 70:
        return ("Exercise caution", [
            "Mixed signals detected - proceed carefully",
            "Verify merchant credentials on marketplace platforms",
            "Use COD or secure payment gateways only",
            "Start with small test orders",
            "Check seller reviews and ratings"
        ])
    elif score < 85:
        return ("High risk - avoid unless verified", [
            "Multiple red flags detected",
            "Merchant verification failed or suspicious",
            "Only use COD if you must proceed",
            "Do not share card/banking details",
            "Report suspicious merchants to platform"
        ])
    else:
        return ("Do not proceed - likely fraudulent", [
            "Critical risk indicators present",
            "Merchant appears to be fraudulent",
            "This appears to be a scam website",
            "Report to platform and authorities",
            "Use established, verified merchants instead"
        ])


async def _with_timeout(coro, layer_name: str, timeout_sec: float, fallback_score: float, fallback_message: str):
    """Execute coroutine with timeout and fallback."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_sec)
    except asyncio.TimeoutError:
        return type("LayerResult", (), {"score": fallback_score, "message": f"{layer_name} timed out"})()
    except Exception as e:
        return type("LayerResult", (), {"score": fallback_score, "message": f"{layer_name}: {fallback_message}"})()


async def evaluate_all(url: str, session=None, weights: Optional[dict] = None) -> tuple[float, List[Reason]]:
    """
    Evaluate URL using all analysis layers.
    
    Args:
        url: URL to analyze
        session: Database session for feedback analysis (optional)
        weights: Custom weights for layers (optional)
    
    Returns:
        Tuple of (risk_score, reasons_list)
    """
    w = weights or DEFAULT_WEIGHTS

    # CRITICAL VETO CHECK: Domain analysis first for typosquatting detection
    d = domain_infra.analyze(url)
    
    # Run async layers concurrently with timeouts
    c_task = _with_timeout(content_ux.analyze(url), "content_ux", 8.0, 15.0, "Content/UX analysis failed")
    v_task = _with_timeout(visual_brand.analyze(url), "visual_brand", 5.0, 5.0, "Visual/brand analysis failed")
    t_task = _with_timeout(threat_intel.analyze(url), "threat_intel", 8.0, 0.0, "Threat intel check failed")
    b_task = _with_timeout(business_verification.analyze(url), "business_verification", 10.0, 25.0, "Business verification failed")
    tech_task = _with_timeout(technical_verification.analyze(url), "technical_verification", 8.0, 15.0, "Technical verification failed")
    merchant_task = _with_timeout(merchant_verification.analyze(url), "merchant_verification", 10.0, 30.0, "Merchant verification failed")
    
    c, v, t, b, tech, merchant = await asyncio.gather(c_task, v_task, t_task, b_task, tech_task, merchant_task)

    # User feedback analysis
    feedback_score = 10.0
    feedback_msg = "No session provided"
    if session is not None:
        fr = user_feedback.summarize_feedback(session, url)
        feedback_score = fr.score
        feedback_msg = fr.message

    # SUSPICIOUS DOMAIN PENALTY: If multiple systems can't analyze the domain, high risk
    analysis_failures = sum(1 for score, msg in [
        (c.score, c.message), (b.score, b.message), (tech.score, tech.message), (merchant.score, merchant.message)
    ] if score >= 25 and any(keyword in msg.lower() for keyword in ["failed", "could not", "timed out", "not found"]))
    
    # If 3+ core systems can't analyze, assume suspicious
    if analysis_failures >= 3:
        suspicion_bonus = 35.0
        d.score = min(100.0, d.score + suspicion_bonus)
        d.message += f"; SUSPICIOUS: {analysis_failures} verification systems failed to analyze domain"

    # Compile all parts with weights
    parts = [
        ("domain_infra", d.score, d.message, w.get("domain_infra", 0.25)),
        ("content_ux", c.score, c.message, w.get("content_ux", 0.10)),
        ("business_verification", b.score, b.message, w.get("business_verification", 0.15)),
        ("technical_verification", tech.score, tech.message, w.get("technical_verification", 0.08)),
        ("merchant_verification", merchant.score, merchant.message, w.get("merchant_verification", 0.30)),
        ("visual_brand", v.score, v.message, w.get("visual_brand", 0.05)),
        ("threat_intel", t.score, t.message, w.get("threat_intel", 0.12)),
        ("user_feedback", feedback_score, feedback_msg, w.get("user_feedback", 0.05)),
    ]

    total = 0.0
    reasons: List[Reason] = []
    for layer, s, msg, weight in parts:
        total += s * weight
        reasons.append(Reason(layer=layer, message=msg, weight=weight, score=s))

    total = max(0.0, min(100.0, total))

    # Apply safety gates
    reason_dicts = [{"layer": r.layer, "message": r.message, "weight": r.weight, "score": r.score} for r in reasons]
    adjusted_score, gated_badge = apply_safety_gates(url, reason_dicts, total)

    return adjusted_score, reasons
