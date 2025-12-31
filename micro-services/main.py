import os
import sys

from dotenv import load_dotenv

# Allow running this service from the repo root (e.g. `uvicorn micro-services.main:app`).
# Adds the `micro-services/` directory to `sys.path` so `news/`, `job_offers/`, etc. can be imported.
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables from the repo root `.env` (needed for Gemini keys, etc.).
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")), override=False)

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict
from news.news_api import check_news_truth
from job_offers.job_main import analyze_job_offer
from fastapi.middleware.cors import CORSMiddleware

import asyncio
from urllib.parse import urlparse
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

# Add imports for analyze route
from urllib.parse import urlparse
from checks import (
    check_domain_age,
    check_ssl_certificate,
    check_logo_similarity,
    detect_suspicious_patterns,
    check_safe_Browse,
    analyze_whois,
    analyze_headers,
    check_broken_links,
)

# Advanced E-commerce Detection imports (switched to ecom_det_fin implementation)
from ecom_det_fin.app.services.scoring import evaluate_all, to_badge, advice_for
from ecom_det_fin.app.services.risk_rules import apply_safety_gates
from ecom_det_fin.app.models.schemas import (
    CheckSiteRequest as EcommerceAnalysisRequest,
    RiskResult,
    FeedbackRequest as EcommerceFeedbackRequest,
    SiteHistoryResponse,
    HistoryPoint,
)
from ecom_det_fin.app.db import init_db as _init_ecom_db, engine as _ecom_engine
from ecom_det_fin.app.models.tables import SiteScan as EcommerceSiteScan, ScanLog
from sqlmodel import Session as SQLSession, select
from datetime import datetime
from datetime import timedelta
from fastapi import Query

# Image detection
# NOTE: torch/transformers often fail to import on Windows if the correct wheels/VC++ runtime
# aren't present. To keep the main backend usable, we lazy-load these deps only when the
# /image/analyze endpoint is called.
_image_model = None
_image_processor = None
_image_model_load_error = None


def _ensure_image_model_loaded():
    global _image_model, _image_processor, _image_model_load_error
    if _image_model is not None and _image_processor is not None:
        return
    if _image_model_load_error is not None:
        raise RuntimeError(_image_model_load_error)

    # Windows-specific: help Python find bundled Torch DLLs first.
    # In some setups (especially with Anaconda-based Python), DLL resolution can pick up
    # conflicting runtimes from PATH, causing WinError 1114 when importing torch.
    try:
        for p in sys.path:
            cand = os.path.join(p, "torch", "lib")
            if os.path.isdir(cand):
                os.add_dll_directory(cand)
                break
    except Exception:
        pass

    try:
        from transformers import AutoModelForImageClassification, AutoImageProcessor
        from PIL import Image  # noqa: F401
        import torch  # noqa: F401
    except Exception as e:
        _image_model_load_error = (
            "Image analysis dependencies failed to import. "
            "Install a working PyTorch build for your Python version/CPU and ensure the "
            "Microsoft Visual C++ Redistributable is installed. Original error: "
            f"{e}"
        )
        raise RuntimeError(_image_model_load_error)

    # Load image model and processor.
    # Prefer a Hugging Face model id and a local cache directory so it works across machines
    # and matches `detect-fake-imagee/download_model2.py`.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_cache_dir = os.path.abspath(
        os.path.join(base_dir, "..", "detect-fake-imagee", "models_cache")
    )
    model_id = os.getenv("AI_IMAGE_MODEL_ID", "Ateeqq/ai-vs-human-image-detector")
    cache_dir = os.getenv("AI_IMAGE_MODEL_CACHE_DIR", default_cache_dir)

    try:
        _image_model = AutoModelForImageClassification.from_pretrained(
            model_id, cache_dir=cache_dir
        )
        _image_processor = AutoImageProcessor.from_pretrained(
            model_id, cache_dir=cache_dir, use_fast=True
        )
    except Exception as e:
        _image_model_load_error = (
            "Failed to load the image model. "
            "If you're offline, run `detect-fake-imagee/download_model2.py` once to cache it. "
            f"Model: {model_id}. Cache dir: {cache_dir}. Error: {e}"
        )
        raise RuntimeError(_image_model_load_error)

class NewsRequest(BaseModel):
    query: str

class JobRequest(BaseModel):
    name: str
    website: str = None
    email: str = None
    phone: str = None
    address: str = None
    job_description: str = None
    salary_offered: str = None
    requirements: str = None
    contact_person: str = None
    company_size: str = None
    industry: str = None
    social_media: Dict[str, Any] = None
    job_post_date: str = None

class UrlRequest(BaseModel):
    url: str

app = FastAPI()


def _safe_log_scan(
    *,
    scan_type: str,
    content: str,
    url: str | None,
    verdict: str,
    risk_score: float,
    extra: dict | None = None,
) -> None:
    """Best-effort scan logging; never breaks the main endpoint."""

    try:
        with SQLSession(_ecom_engine) as session:
            row = ScanLog(
                scan_type=scan_type,
                content=content,
                url=url,
                verdict=verdict,
                risk_score=float(risk_score),
                created_at=datetime.utcnow(),
                extra_json=json.dumps(extra or {}),
            )
            session.add(row)
            session.commit()
    except Exception:
        # Intentionally swallow all errors to keep API stable.
        return


@app.on_event("startup")
def _startup_init_db():
    # Enable real persistence for advanced e-commerce scans + history.
    # Uses ecom_det_fin SQLite DB by default: sqlite:///data/app.db
    _init_ecom_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 

@app.post("/news/verify")
def verify_news(request: NewsRequest):
    try:
        result = check_news_truth(request.query)
        verdict_overall = (result or {}).get("verdict") or "Uncertain"
        verdict_norm = str(verdict_overall).strip().lower()
        if verdict_norm == "true":
            ui_verdict = "Authentic"
            risk_score = 10.0
        elif verdict_norm == "false":
            ui_verdict = "Fake"
            risk_score = 90.0
        elif verdict_norm == "error":
            ui_verdict = "Error"
            risk_score = 50.0
        else:
            ui_verdict = "Suspicious"
            risk_score = 50.0

        _safe_log_scan(
            scan_type="Fake News",
            content=(request.query or "")[:300],
            url=None,
            verdict=ui_verdict,
            risk_score=risk_score,
            extra={"source": "news/verify", "raw_verdict": verdict_overall},
        )
        return {"result": result}
    except Exception as e:
        # Return a stable shape so the frontend can render an error state without breaking.
        return {
            "result": {
                "verdict": "Error",
                "explanation": str(e),
                "parsed_output": {
                    "verdict_overall": "Uncertain",
                    "claims": [],
                    "sources_used": [],
                    "explanation": "",
                },
                "grounding_metadata": {
                    "search_queries": [],
                    "sources": [],
                    "claims_analysis": [],
                },
            }
        }

@app.post("/job/analyze")
def analyze_job(request: JobRequest):
    try:
        result = analyze_job_offer(request.dict())
        payload = result.dict()
        confidence = float(payload.get("confidence_score") or 0.0)
        risk_level = str(payload.get("risk_level") or "").upper()
        if risk_level in {"CRITICAL", "HIGH"}:
            verdict = "Scam"
        elif risk_level == "MEDIUM":
            verdict = "Suspicious"
        else:
            verdict = "Safe"

        content = payload.get("final_prediction_reason") or (request.job_description or "")
        _safe_log_scan(
            scan_type="Job Posting",
            content=str(content)[:300],
            url=str(request.website) if request.website else None,
            verdict=verdict,
            risk_score=confidence,
            extra={"source": "job/analyze", "risk_level": risk_level},
        )
        return {"result": payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"message": "✅ Fake E-commerce Website Detector is running!"}


class UrlRequest(BaseModel):
    url: str

@app.post("/analyze")
async def analyze(data: UrlRequest):
    url = data.url
    try:
        # ✅ Validate and extract domain
        parsed_url = urlparse(url)
        domain_name = parsed_url.netloc.replace("www.", "") if parsed_url.netloc else parsed_url.path
        if not domain_name:
            raise HTTPException(status_code=400, detail="Invalid URL provided.")

        # ✅ Create a list of all check tasks to run concurrently
        async with httpx.AsyncClient() as client:
            tasks = [
                check_domain_age(domain_name),
                check_ssl_certificate(domain_name),
                check_logo_similarity(url, client),
                detect_suspicious_patterns(url, client),
                check_safe_Browse(url, client),
                analyze_whois(domain_name),
                analyze_headers(url, client),
                check_broken_links(url, client),
            ]
            
            # ✅ Run all checks at the same time
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assign results safely, handling potential exceptions
        (
            domain_info, ssl_info, logo_info, pattern_info,
            safe_Browse_info, whois_info, headers_info, link_info
        ) = [res if not isinstance(res, Exception) else {"error": str(res), "suspicious": True} for res in results]

        # ✅ Final risk score calculation
        risk_score = sum([
            int(info.get('suspicious', False) or info.get('is_suspicious', False))
            for info in [domain_info, ssl_info, logo_info, pattern_info, safe_Browse_info, whois_info, headers_info, link_info]
        ])
        
        # ✅ Final verdict
        verdict = "Unsafe" if risk_score >= 3 else "Safe"

        payload = {
            "domain": domain_info,
            "ssl": ssl_info,
            "logo": logo_info,
            "patterns": pattern_info,
            "safe_Browse": safe_Browse_info,
            "whois": whois_info,
            "headers": headers_info,
            "links": link_info,
            "risk_score": risk_score,
            "verdict": verdict,
        }

        # Convert 0..8 checks into a 0..100-ish score for UI consistency.
        risk_percent = float(min(100.0, max(0.0, risk_score * 12.5)))
        _safe_log_scan(
            scan_type="E-commerce",
            content=domain_name,
            url=str(url),
            verdict="High Risk" if verdict == "Unsafe" else "Verified Safe",
            risk_score=risk_percent,
            extra={"source": "analyze", "raw_risk_score": risk_score, "raw_verdict": verdict},
        )

        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/image/analyze")
async def analyze_image(file: UploadFile = File(...)):
    try:
        _ensure_image_model_loaded()
        from PIL import Image
        import torch
        import io

        # Read and preprocess image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        inputs = _image_processor(images=image, return_tensors="pt")

        # Inference
        with torch.no_grad():
            outputs = _image_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

        labels = _image_model.config.id2label
        # Map raw label->probability
        result = {str(labels[i]): float(p) for i, p in enumerate(probs[0])}
        print("image model raw labels:", result)

        # Normalize: ensure 'ai' and 'human' keys exist
        lower_map = {str(k).lower(): v for k, v in result.items()}
        ai_synonyms = {"ai", "fake", "generated", "synthetic"}
        human_synonyms = {"human", "hum", "real", "natural", "person", "people", "photo", "photograph"}

        ai_score = None
        human_score = None
        for key, val in lower_map.items():
            if any(s in key for s in ai_synonyms):
                ai_score = val
            if any(s in key for s in human_synonyms):
                human_score = val

        # Binary fallback: infer missing class as 1 - other when exactly 2 classes
        if len(result) == 2:
            if ai_score is not None and human_score is None:
                human_score = 1.0 - ai_score
            elif human_score is not None and ai_score is None:
                ai_score = 1.0 - human_score

        # General fallback: choose top-2 classes if still missing
        if ai_score is None or human_score is None:
            sorted_probs = sorted(result.items(), key=lambda x: x[1], reverse=True)
            if ai_score is None and len(sorted_probs) > 0:
                ai_score = sorted_probs[0][1]
            if human_score is None and len(sorted_probs) > 1:
                human_score = sorted_probs[1][1]

        # Clamp and build normalized
        ai_val = max(0.0, min(1.0, ai_score)) if ai_score is not None else 0.0
        human_val = max(0.0, min(1.0, human_score)) if human_score is not None else 0.0
        normalized = {"ai": ai_val, "human": human_val}

        # Metadata extraction (best-effort)
        meta = {}
        try:
            exif_data = image.getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = Image.ExifTags.TAGS.get(tag_id, tag_id)
                    meta[str(tag)] = str(value)
            else:
                meta = None
        except Exception:
            meta = None

        ai_percent = float(round(normalized.get("ai", 0.0) * 100.0, 2))
        ui_verdict = "AI Generated" if normalized.get("ai", 0.0) >= 0.5 else "Human Made"

        payload = {"prediction": normalized, "labels": result, "metadata": meta}
        print("image model payload:", payload)

        _safe_log_scan(
            scan_type="AI Image",
            content=str(getattr(file, "filename", "image"))[:300],
            url=None,
            verdict=ui_verdict,
            risk_score=ai_percent,
            extra={"source": "image/analyze"},
        )
        return JSONResponse(content=payload)
    except HTTPException:
        raise
    except Exception as e:
        # If torch/transformers can't load (common on Windows), keep a clear actionable error.
        raise HTTPException(status_code=503, detail=f"Image analysis unavailable: {str(e)}")


# Advanced E-commerce Detection Endpoints
@app.post("/ecommerce/analyze-advanced", response_model=dict)
async def analyze_ecommerce_advanced(request: EcommerceAnalysisRequest):
    """
    Advanced e-commerce website analysis using 8-layer verification system.
    Provides comprehensive risk assessment with detailed explanations.
    """
    try:
        with SQLSession(_ecom_engine) as session:
            # Run the comprehensive analysis (real-time)
            score, reasons = await evaluate_all(str(request.url), session=session)

            # Apply safety gates to align with ecom_det_fin behavior
            reason_list = [
                {"layer": r.layer, "message": r.message, "weight": r.weight, "score": r.score}
                for r in reasons
            ]
            adjusted_score, gated_badge = apply_safety_gates(str(request.url), reason_list, score)
            payment, actions = advice_for(adjusted_score)

            scan = EcommerceSiteScan(
                url=str(request.url),
                risk_score=adjusted_score,
                badge=gated_badge,
                reasons_json=json.dumps(reason_list),
                scanned_at=datetime.utcnow(),
            )
            session.add(scan)
            session.commit()

            try:
                _safe_log_scan(
                    scan_type="E-commerce",
                    content=urlparse(str(request.url)).netloc.replace("www.", "") or str(request.url),
                    url=str(request.url),
                    verdict=gated_badge,
                    risk_score=float(adjusted_score),
                    extra={"source": "ecommerce/analyze-advanced", "analysis_type": "advanced"},
                )
            except Exception:
                pass

            return {
                "url": request.url,
                "risk_score": adjusted_score,
                "badge": gated_badge,
                "reasons": reason_list,
                "advice": {"payment": payment, "actions": actions},
                "scanned_at": scan.scanned_at.isoformat(),
                "analysis_type": "advanced",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced e-commerce analysis failed: {str(e)}")


def _icon_for_type(scan_type: str) -> str:
    t = (scan_type or "").lower()
    if "news" in t:
        return "📰"
    if "e-commerce" in t or "ecommerce" in t:
        return "🛍️"
    if "job" in t:
        return "🧑‍💼"
    if "image" in t:
        return "📷"
    return "📊"


@app.get("/api/history")
def api_history(limit: int = Query(50, ge=1, le=200)):
    try:
        with SQLSession(_ecom_engine) as session:
            rows = session.exec(
                select(ScanLog).order_by(ScanLog.created_at.desc()).limit(limit)
            ).all()

        return {
            "items": [
                {
                    "id": str(r.id),
                    "type": r.scan_type,
                    "content": r.content,
                    "url": r.url,
                    "verdict": r.verdict,
                    "riskScore": float(r.risk_score),
                    "timestamp": r.created_at.isoformat(),
                    "icon": _icon_for_type(r.scan_type),
                }
                for r in rows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History lookup failed: {str(e)}")


@app.delete("/api/history/{scan_id}")
def api_delete_history_item(scan_id: int):
    try:
        with SQLSession(_ecom_engine) as session:
            row = session.get(ScanLog, scan_id)
            if row is None:
                raise HTTPException(status_code=404, detail="History item not found")
            session.delete(row)
            session.commit()
        return {"status": "deleted", "id": scan_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@app.get("/api/stats")
def api_stats():
    try:
        now = datetime.utcnow()
        today_start = datetime(year=now.year, month=now.month, day=now.day)

        fake_verdicts = {
            "fake",
            "scam",
            "ai generated",
            "deepfake",
            "high risk",
            "critical risk",
            "unsafe",
        }
        safe_verdicts = {
            "safe",
            "verified safe",
            "authentic",
            "low risk",
            "human made",
            "human written",
        }

        with SQLSession(_ecom_engine) as session:
            all_rows = session.exec(select(ScanLog)).all()

        total = len(all_rows)
        scans_today = sum(1 for r in all_rows if r.created_at >= today_start)
        fake_detected = sum(1 for r in all_rows if (r.verdict or "").strip().lower() in fake_verdicts)
        safe_content = sum(1 for r in all_rows if (r.verdict or "").strip().lower() in safe_verdicts)
        accuracy = round((safe_content / total) * 100.0, 2) if total else 0.0

        return {
            "scansToday": scans_today,
            "accuracy": accuracy,
            "totalScans": total,
            "fakeDetected": fake_detected,
            "safeContent": safe_content,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats lookup failed: {str(e)}")


@app.get("/api/site-history", response_model=SiteHistoryResponse)
async def ecommerce_site_history(url: str):
    try:
        with SQLSession(_ecom_engine) as session:
            q = (
                select(EcommerceSiteScan)
                .where(EcommerceSiteScan.url == str(url))
                .order_by(EcommerceSiteScan.scanned_at.asc())
            )
            rows = session.exec(q).all()
        if not rows:
            raise HTTPException(status_code=404, detail="No scans for this URL yet")
        timeline = [HistoryPoint(scanned_at=r.scanned_at, risk_score=r.risk_score, badge=r.badge) for r in rows]
        return SiteHistoryResponse(url=url, timeline=timeline)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History lookup failed: {str(e)}")


@app.post("/ecommerce/feedback")
async def submit_ecommerce_feedback(request: EcommerceFeedbackRequest):
    """
    Submit feedback about an e-commerce transaction.
    This helps improve the accuracy of future analyses.
    """
    try:
        # For now, just acknowledge the feedback
        # In a full implementation, this would store feedback in database
        return {
            "status": "success",
            "message": f"Feedback recorded for {request.url}",
            "delivered": request.delivered,
            "order_hash": request.order_hash
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


@app.get("/ecommerce/compare")
async def compare_analysis_methods(url: str):
    """
    Compare basic vs advanced e-commerce analysis for the same URL.
    Useful for understanding the difference in analysis depth.
    """
    try:
        # Basic analysis (existing method)
        basic_result = await analyze(UrlRequest(url=url))

        # Advanced analysis
        advanced_result = await analyze_ecommerce_advanced(EcommerceAnalysisRequest(url=url))

        return {
            "url": url,
            "basic_analysis": {
                "risk_score": basic_result["risk_score"],
                "verdict": basic_result["verdict"],
                "checks_count": len([k for k in basic_result.keys() if k not in ["risk_score", "verdict"]]),
            },
            "advanced_analysis": {
                "risk_score": advanced_result["risk_score"],
                "badge": advanced_result["badge"],
                "layers_count": len(advanced_result["reasons"]),
                "has_advice": bool(advanced_result["advice"]),
            },
            "comparison": {
                "score_difference": abs(advanced_result["risk_score"] - basic_result["risk_score"]),
                "analysis_depth": "advanced" if len(advanced_result["reasons"]) > 5 else "basic",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison analysis failed: {str(e)}")
