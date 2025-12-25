from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
import json

from ..db import get_session
from ..models.schemas import CheckSiteRequest, RiskResult, FeedbackRequest, SiteHistoryResponse, HistoryPoint
from ..models.tables import SiteScan, Feedback
from ..services.scoring import evaluate_all, to_badge, advice_for
from ..services.risk_rules import apply_safety_gates

router = APIRouter(prefix="/api", tags=["ecommerce"])

@router.post("/check-site", response_model=RiskResult)
async def check_site(payload: CheckSiteRequest, session: Session = Depends(get_session)):
    score, reasons = await evaluate_all(str(payload.url), session=session)
    badge = to_badge(score)
    # Apply safety gates to enforce conservative classification
    reason_dicts = [{"layer": r.layer, "message": r.message, "weight": r.weight, "score": r.score} for r in reasons]
    adjusted_score, gated_badge = apply_safety_gates(str(payload.url), reason_dicts, score)
    badge = gated_badge
    payment, actions = advice_for(adjusted_score)

    scan = SiteScan(
        url=str(payload.url),
        risk_score=adjusted_score,
        badge=badge,
        reasons_json=json.dumps([r.__dict__ for r in reasons]),
        scanned_at=datetime.utcnow(),
    )
    session.add(scan)
    session.commit()

    return RiskResult(
        url=payload.url,
        risk_score=adjusted_score,
        badge=badge,
        reasons=[
            # reconstruct Reason-like dicts for the API model
            {"layer": r.layer, "message": r.message, "weight": r.weight, "score": r.score}
            for r in reasons
        ],
        advice={"payment": payment, "actions": actions},
        scanned_at=scan.scanned_at,
    )


@router.post("/feedback")
async def submit_feedback(payload: FeedbackRequest, session: Session = Depends(get_session)):
    fb = Feedback(url=str(payload.url), delivered=payload.delivered, order_hash=payload.order_hash)
    session.add(fb)
    session.commit()
    return {"status": "ok", "message": "Feedback recorded"}


@router.get("/site-history", response_model=SiteHistoryResponse)
async def site_history(url: str, session: Session = Depends(get_session)):
    q = select(SiteScan).where(SiteScan.url == url).order_by(SiteScan.scanned_at.asc())
    rows = session.exec(q).all()
    if not rows:
        raise HTTPException(status_code=404, detail="No scans for this URL yet")
    timeline = [HistoryPoint(scanned_at=r.scanned_at, risk_score=r.risk_score, badge=r.badge) for r in rows]
    return SiteHistoryResponse(url=url, timeline=timeline)
