from __future__ import annotations
from dataclasses import dataclass
from sqlmodel import Session, select
from ...models.tables import Feedback

@dataclass
class LayerResult:
    score: float
    message: str


def summarize_feedback(session: Session, url: str) -> LayerResult:
    # Aggregate simple signal: ratio of non-deliveries vs deliveries
    q = select(Feedback).where(Feedback.url == url)
    items = session.exec(q).all()
    if not items:
        return LayerResult(score=5.0, message="No user feedback yet")

    delivered = sum(1 for i in items if i.delivered)
    failed = sum(1 for i in items if not i.delivered)

    if failed == 0:
        return LayerResult(score=0.0, message=f"{delivered} verified deliveries, no failures")
    total = delivered + failed
    # Risk scaled by failure ratio
    ratio = failed / total
    score = min(100.0, 80.0 * ratio)
    return LayerResult(score=score, message=f"Feedback: {failed} failures / {total} reports")
