import os
import sys
import logging

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

# Ensure local modules (e.g., news/, job_offers/, checks.py) are importable when
# running via Uvicorn from the repo root on Windows.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load environment variables from .env (repo root and micro-services/) so
# downstream modules that use os.getenv() can access them.
if load_dotenv is not None:
    repo_root = os.path.abspath(os.path.join(BASE_DIR, ".."))
    load_dotenv(os.path.join(repo_root, ".env"), override=False)
    load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict
from news.news_api import check_news_truth, GeminiQuotaError
from job_offers.job_main import analyze_job_offer
from fastapi.middleware.cors import CORSMiddleware

import asyncio
from urllib.parse import urlparse
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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
)
from datetime import datetime
# Image detection imports
from PIL import Image, UnidentifiedImageError
import io


logger = logging.getLogger(__name__)


torch = None
image_model = None
image_processor = None
_image_model_error: str | None = None
_image_model_loaded = False

# Image model location strategy:
# - Prefer local cache created by detect-fake-imagee/download_model2.py (models_cache)
# - Fall back to the original snapshot-style directory if present
image_model_cache_dir = os.path.join(BASE_DIR, "..", "detect-fake-imagee", "models_cache")
image_model_snapshot_root = os.path.join(
    BASE_DIR,
    "..",
    "detect-fake-imagee",
    "ai-image-detector-model2",
    "models--Ateeqq--ai-vs-human-image-detector",
    "snapshots",
)

# Hugging Face model id
IMAGE_MODEL_ID = "Ateeqq/ai-vs-human-image-detector"

def _ensure_image_model_loaded() -> None:
    """Lazy-load the image detection model.

    On some Windows setups, importing torch at process startup can fail due to
    missing DLL dependencies (WinError 1114). We load on-demand so the API can
    still boot and serve non-image endpoints.
    """
    global torch, image_model, image_processor, _image_model_error, _image_model_loaded

    if _image_model_loaded or _image_model_error:
        return

    try:
        import torch as _torch
        from transformers import AutoModelForImageClassification, AutoImageProcessor

        # 1) Prefer local cache directory (created by download_model2.py)
        if os.path.isdir(image_model_cache_dir) and os.listdir(image_model_cache_dir):
            image_model = AutoModelForImageClassification.from_pretrained(
                IMAGE_MODEL_ID,
                cache_dir=image_model_cache_dir,
            )
            image_processor = AutoImageProcessor.from_pretrained(
                IMAGE_MODEL_ID,
                cache_dir=image_model_cache_dir,
                use_fast=True,
            )
        # 2) If snapshot-style folder exists, load from the first snapshot
        elif os.path.isdir(image_model_snapshot_root):
            snapshots = [
                d for d in os.listdir(image_model_snapshot_root)
                if os.path.isdir(os.path.join(image_model_snapshot_root, d))
            ]
            if not snapshots:
                raise RuntimeError(f"No snapshot directories found in {image_model_snapshot_root}")
            snapshot_dir = os.path.join(image_model_snapshot_root, snapshots[0])

            image_model = AutoModelForImageClassification.from_pretrained(snapshot_dir)
            image_processor = AutoImageProcessor.from_pretrained(snapshot_dir, use_fast=True)
        # 3) Last resort: download to cache dir
        else:
            os.makedirs(image_model_cache_dir, exist_ok=True)
            image_model = AutoModelForImageClassification.from_pretrained(
                IMAGE_MODEL_ID,
                cache_dir=image_model_cache_dir,
            )
            image_processor = AutoImageProcessor.from_pretrained(
                IMAGE_MODEL_ID,
                cache_dir=image_model_cache_dir,
                use_fast=True,
            )

        torch = _torch
        _image_model_loaded = True
    except Exception as e:
        # Keep full exception type for easier debugging (e.g., torch DLL load errors on Windows)
        _image_model_error = f"{type(e).__name__}: {e}"

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
        return {"result": result}
    except GeminiQuotaError as e:
        raise HTTPException(
            status_code=429,
            detail=(
                "Gemini API quota exhausted for this project/key. "
                "Check https://ai.dev/usage?tab=rate-limit and your billing/plan. "
                f"Raw error: {str(e)}"
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/job/analyze")
def analyze_job(request: JobRequest):
    try:
        result = analyze_job_offer(request.dict())
        return {"result": result.dict()}
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

        return {
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/image/analyze")
async def analyze_image(file: UploadFile = File(...)):
    try:
        _ensure_image_model_loaded()
        if _image_model_error or not _image_model_loaded or image_model is None or image_processor is None or torch is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Image model unavailable in this environment. "
                    "If you see a torch DLL error on Windows, install the Microsoft Visual C++ Redistributable "
                    "and reinstall a compatible PyTorch build. "
                    f"Underlying error: {_image_model_error}"
                ),
            )

        # Read and preprocess image
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="No file content received.")

        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
        except UnidentifiedImageError:
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
        inputs = image_processor(images=image, return_tensors="pt")

        # Inference
        with torch.no_grad():
            outputs = image_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

        labels = image_model.config.id2label
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

        payload = {"prediction": normalized, "labels": result, "metadata": meta}
        print("image model payload:", payload)
        return JSONResponse(content=payload)
    except HTTPException:
        raise
    except Exception as e:
        # Preserve stack trace in server logs while returning a clean error to clients.
        logger.exception("Image analysis failed")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {type(e).__name__}: {e}")


# Advanced E-commerce Detection Endpoints
@app.post("/ecommerce/analyze-advanced", response_model=dict)
async def analyze_ecommerce_advanced(request: EcommerceAnalysisRequest):
    """
    Advanced e-commerce website analysis using 8-layer verification system.
    Provides comprehensive risk assessment with detailed explanations.
    """
    try:
        # Run the comprehensive analysis
        score, reasons = await evaluate_all(str(request.url), session=None)

        # Apply safety gates to align with ecom_det_fin behavior
        reason_list = [
            {"layer": r.layer, "message": r.message, "weight": r.weight, "score": r.score}
            for r in reasons
        ]
        adjusted_score, gated_badge = apply_safety_gates(str(request.url), reason_list, score)
        payment, actions = advice_for(adjusted_score)

        return {
            "url": request.url,
            "risk_score": adjusted_score,
            "badge": gated_badge,
            "reasons": reason_list,
            "advice": {"payment": payment, "actions": actions},
            "scanned_at": datetime.utcnow().isoformat(),
            "analysis_type": "advanced",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced e-commerce analysis failed: {str(e)}")


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
