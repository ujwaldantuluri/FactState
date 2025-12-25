from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
import json
import hashlib
import uuid

from ..db import get_session
from ..models.tables import VerifiedFeedback, UserReputationScore, FeedbackStatus
from ..services.verified_feedback import VerifiedFeedbackAPI, ProofType
from pydantic import BaseModel

router = APIRouter(prefix="/api/verified-feedback", tags=["Verified Feedback"])

# Pydantic models for API
class OrderDetails(BaseModel):
    order_id: str
    payment_id: str
    amount: float
    order_date: datetime
    product_name: str
    product_description: Optional[str] = None
    expected_delivery: Optional[datetime] = None

class FeedbackOutcome(BaseModel):
    delivered: bool
    delivery_quality: Optional[int] = None  # 1-5 rating
    payment_issues: bool = False
    product_matches_description: Optional[bool] = None
    delivery_date: Optional[datetime] = None
    additional_notes: Optional[str] = None

class ProofFileMetadata(BaseModel):
    filename: str
    file_type: str
    proof_type: ProofType
    timestamp: float
    file_size: int

verified_feedback_api = VerifiedFeedbackAPI()

@router.post("/submit")
async def submit_verified_feedback(
    url: str = Form(...),
    user_identifier: str = Form(...),  # Anonymous but consistent identifier
    order_details: str = Form(...),  # JSON string
    outcome: str = Form(...),  # JSON string
    proof_files: List[UploadFile] = File(...),
    proof_metadata: str = Form(...),  # JSON string with metadata for each file
    session: Session = Depends(get_session)
):
    """
    Submit verified feedback with comprehensive proof requirements
    
    Required proof files:
    - Order screenshot/confirmation
    - Payment receipt
    - Delivery notification OR explanation for non-delivery
    """
    
    try:
        # Parse JSON inputs
        order_data = json.loads(order_details)
        outcome_data = json.loads(outcome)
        metadata_list = json.loads(proof_metadata)
        
        # Validate minimum requirements
        if len(proof_files) < 2:
            raise HTTPException(
                status_code=400, 
                detail="Minimum 2 proof files required (order confirmation + payment receipt)"
            )
        
        # Process uploaded files
        processed_proofs = []
        for i, file in enumerate(proof_files):
            # Read and hash file content
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Get metadata for this file
            file_metadata = metadata_list[i] if i < len(metadata_list) else {}
            file_metadata.update({
                'file_size': len(content),
                'upload_timestamp': datetime.utcnow().timestamp()
            })
            
            processed_proofs.append({
                'type': file_metadata.get('proof_type', 'order_screenshot'),
                'hash': file_hash,
                'metadata': file_metadata
            })
            
            # Store file securely (in production, use cloud storage)
            # For now, just validate the hash
        
        # Submit to verification system
        result = await verified_feedback_api.submit_feedback(
            url=url,
            user_id=user_identifier,
            order_details=order_data,
            proof_files=processed_proofs,
            outcome=outcome_data
        )
        
        return {
            "success": True,
            "verification_status": result["status"],
            "message": result["message"],
            "feedback_id": result.get("feedback_id"),
            "verification_score": result.get("verification_score", 0),
            "estimated_review_time": _get_estimated_review_time(result["status"])
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")

@router.get("/requirements")
async def get_verification_requirements():
    """Get detailed requirements for feedback verification"""
    
    return {
        "required_documents": {
            "for_delivered_orders": [
                {
                    "type": "order_screenshot",
                    "description": "Screenshot of order confirmation page",
                    "required_elements": ["Order ID", "Product name", "Amount", "Merchant name"],
                    "accepted_formats": ["PNG", "JPG", "PDF"]
                },
                {
                    "type": "payment_receipt",
                    "description": "Payment confirmation from bank/gateway",
                    "required_elements": ["Transaction ID", "Amount", "Date", "Merchant"],
                    "accepted_formats": ["PNG", "JPG", "PDF"]
                },
                {
                    "type": "delivery_notification",
                    "description": "Delivery confirmation or tracking update",
                    "required_elements": ["Delivery date", "Address", "Tracking number"],
                    "accepted_formats": ["PNG", "JPG", "PDF"]
                }
            ],
            "for_scam_reports": [
                {
                    "type": "order_screenshot",
                    "description": "Screenshot of order confirmation page",
                    "required_elements": ["Order ID", "Product name", "Amount", "Merchant name"],
                    "accepted_formats": ["PNG", "JPG", "PDF"]
                },
                {
                    "type": "payment_receipt", 
                    "description": "Proof of payment made",
                    "required_elements": ["Transaction ID", "Amount", "Date", "Merchant"],
                    "accepted_formats": ["PNG", "JPG", "PDF"]
                },
                {
                    "type": "email_confirmation",
                    "description": "Email communications with merchant",
                    "required_elements": ["Email addresses", "Dates", "Response attempts"],
                    "accepted_formats": ["PNG", "JPG", "PDF", "EML"]
                }
            ]
        },
        "verification_process": {
            "steps": [
                "Document upload and hashing",
                "Automated validation of order details",
                "OCR extraction of key information",
                "Cross-validation of data consistency", 
                "Manual review by verification team",
                "Final scoring and impact calculation"
            ],
            "timeline": "2-5 business days for standard verification",
            "appeal_process": "Available for rejected verifications"
        },
        "privacy_protection": {
            "data_anonymization": "Personal details are hashed and anonymized",
            "file_encryption": "All proof files are encrypted at rest",
            "retention_policy": "Verification data retained for 2 years maximum",
            "user_rights": "Right to deletion and data export available"
        }
    }

@router.get("/status")
async def list_verification_status(
    url: str,
    session: Session = Depends(get_session)
):
    """List verification records for a URL (lightweight summary for UI)."""
    rows = session.exec(
        select(VerifiedFeedback).where(VerifiedFeedback.url == url)
    ).all()

    out = []
    for r in rows:
        rep = session.exec(
            select(UserReputationScore).where(UserReputationScore.user_id == r.user_id)
        ).first()
        doc_status = (
            "verified" if r.status in [FeedbackStatus.VERIFIED_DELIVERED, FeedbackStatus.VERIFIED_SCAM] else
            "pending" if r.status in [FeedbackStatus.PENDING_VERIFICATION] else
            "failed"
        )
        out.append({
            "id": r.id,
            "url": r.url,
            "verification_status": r.status,
            "document_verification_status": doc_status,
            "user_reputation_score": rep.reputation_score if rep else 50.0,
            "created_at": r.submission_time,
            "updated_at": r.submission_time,
        })
    return out

@router.get("/status/{feedback_id}")
async def get_verification_status(
    feedback_id: int,
    session: Session = Depends(get_session)
):
    """Check verification status of submitted feedback"""
    
    feedback = session.get(VerifiedFeedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return {
        "feedback_id": feedback_id,
        "status": feedback.status,
        "verification_score": feedback.verification_score,
        "weight": feedback.weight,
        "submission_time": feedback.submission_time,
        "review_notes": feedback.verification_notes,
        "estimated_completion": _get_estimated_completion(feedback)
    }

@router.get("/user/{user_id}/reputation")
async def get_user_reputation(
    user_id: str,
    session: Session = Depends(get_session)
):
    """Get user's feedback reputation score"""
    
    reputation = session.exec(
        select(UserReputationScore).where(UserReputationScore.user_id == user_id)
    ).first()
    
    if not reputation:
        # Create new reputation record
        reputation = UserReputationScore(user_id=user_id)
        session.add(reputation)
        session.commit()
        session.refresh(reputation)
    
    return {
        "user_id": user_id,
        "reputation_score": reputation.reputation_score,
        "total_feedbacks": reputation.total_feedbacks,
        "verified_feedbacks": reputation.verified_feedbacks,
        "false_reports": reputation.false_reports,
        "trust_level": _calculate_trust_level(reputation.reputation_score),
        "feedback_weight_multiplier": min(2.0, reputation.reputation_score / 50.0)
    }

@router.post("/admin/verify/{feedback_id}")
async def admin_verify_feedback(
    feedback_id: int,
    verification_decision: str = Form(...),  # "approve", "reject", "request_more_info"
    reviewer_notes: Optional[str] = Form(None),
    reviewer_id: str = Form(...),
    session: Session = Depends(get_session)
):
    """Admin endpoint for manual verification of feedback"""
    
    feedback = session.get(VerifiedFeedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    if verification_decision == "approve":
        if feedback.delivered_successfully:
            feedback.status = FeedbackStatus.VERIFIED_DELIVERED
        else:
            feedback.status = FeedbackStatus.VERIFIED_SCAM
    elif verification_decision == "reject":
        feedback.status = FeedbackStatus.REJECTED
    else:
        feedback.status = FeedbackStatus.PENDING_VERIFICATION
    
    feedback.verification_notes = reviewer_notes
    feedback.reviewer_id = reviewer_id
    
    # Update user reputation based on verification outcome
    _update_user_reputation(feedback.user_id, feedback.status, session)
    
    session.add(feedback)
    session.commit()
    
    return {
        "success": True,
        "feedback_id": feedback_id,
        "new_status": feedback.status,
        "message": "Verification completed successfully"
    }

def _get_estimated_review_time(status: FeedbackStatus) -> str:
    """Get estimated review time based on status"""
    if status == FeedbackStatus.VERIFICATION_FAILED:
        return "N/A - Verification failed"
    elif status in [FeedbackStatus.VERIFIED_DELIVERED, FeedbackStatus.VERIFIED_SCAM]:
        return "Completed"
    else:
        return "2-5 business days"

def _get_estimated_completion(feedback: VerifiedFeedback) -> Optional[datetime]:
    """Calculate estimated completion time"""
    if feedback.status in [FeedbackStatus.VERIFIED_DELIVERED, FeedbackStatus.VERIFIED_SCAM, FeedbackStatus.REJECTED]:
        return None
    
    # Estimate based on current queue and complexity
    from datetime import timedelta
    return feedback.submission_time + timedelta(days=3)

def _calculate_trust_level(reputation_score: float) -> str:
    """Calculate user trust level"""
    if reputation_score >= 80:
        return "Highly Trusted"
    elif reputation_score >= 60:
        return "Trusted"
    elif reputation_score >= 40:
        return "Neutral"
    elif reputation_score >= 20:
        return "Low Trust"
    else:
        return "Untrusted"

def _update_user_reputation(user_id: str, status: FeedbackStatus, session: Session):
    """Update user reputation based on verification outcome"""
    reputation = session.exec(
        select(UserReputationScore).where(UserReputationScore.user_id == user_id)
    ).first()
    
    if not reputation:
        reputation = UserReputationScore(user_id=user_id)
        session.add(reputation)
    
    reputation.total_feedbacks += 1
    
    if status in [FeedbackStatus.VERIFIED_DELIVERED, FeedbackStatus.VERIFIED_SCAM]:
        reputation.verified_feedbacks += 1
        reputation.reputation_score = min(100.0, reputation.reputation_score + 2.0)
    elif status == FeedbackStatus.REJECTED:
        reputation.false_reports += 1
        reputation.reputation_score = max(0.0, reputation.reputation_score - 5.0)
    
    reputation.updated_at = datetime.utcnow()
    session.commit()