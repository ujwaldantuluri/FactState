from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

# Import from models instead of redefining
from ..models.tables import VerifiedFeedback, UserReputationScore, FeedbackStatus

class ProofType(str, Enum):
    ORDER_SCREENSHOT = "order_screenshot"
    DELIVERY_NOTIFICATION = "delivery_notification"
    PAYMENT_RECEIPT = "payment_receipt"
    BANK_STATEMENT = "bank_statement"
    EMAIL_CONFIRMATION = "email_confirmation"
    TRACKING_INFO = "tracking_info"

@dataclass
class VerificationProof:
    proof_type: ProofType
    file_hash: str
    metadata: Dict
    confidence_score: float

class FeedbackVerifier:
    """Comprehensive feedback verification system"""
    
    def __init__(self):
        self.required_proofs = {
            FeedbackStatus.VERIFIED_DELIVERED: [
                ProofType.ORDER_SCREENSHOT,
                ProofType.DELIVERY_NOTIFICATION,
                ProofType.PAYMENT_RECEIPT
            ],
            FeedbackStatus.VERIFIED_SCAM: [
                ProofType.ORDER_SCREENSHOT,
                ProofType.PAYMENT_RECEIPT,
                ProofType.EMAIL_CONFIRMATION
            ]
        }
    
    async def verify_order_details(self, feedback: VerifiedFeedback) -> float:
        """Verify order details consistency"""
        score = 0.0
        
        # Check required fields
        required_fields = [
            feedback.order_id, feedback.payment_id, 
            feedback.order_amount, feedback.order_date
        ]
        
        if all(field is not None for field in required_fields):
            score += 25.0
        
        # Validate order ID format
        if feedback.order_id and self._validate_order_id_format(feedback.order_id):
            score += 15.0
        
        # Validate payment ID format
        if feedback.payment_id and self._validate_payment_id_format(feedback.payment_id):
            score += 15.0
        
        # Check amount reasonableness
        if feedback.order_amount and 10 <= feedback.order_amount <= 100000:
            score += 10.0
        
        # Check date consistency
        if self._validate_date_consistency(feedback):
            score += 15.0
        
        # Product details completeness
        if feedback.product_name and feedback.product_description:
            score += 20.0
        
        return score
    
    def _validate_order_id_format(self, order_id: str) -> bool:
        """Validate order ID follows common e-commerce patterns"""
        patterns = [
            r'^[A-Z]{2,3}[0-9]{6,12}$',  # AM123456789
            r'^[0-9]{8,16}$',            # 1234567890123456
            r'^ORD-[A-Z0-9]{6,10}$',     # ORD-ABC123
            r'^[0-9]{4}-[0-9]{4}-[0-9]{4}$'  # 1234-5678-9012
        ]
        
        return any(re.match(pattern, order_id) for pattern in patterns)
    
    def _validate_payment_id_format(self, payment_id: str) -> bool:
        """Validate payment ID follows payment gateway patterns"""
        patterns = [
            r'^pay_[A-Za-z0-9]{14,}$',    # Razorpay
            r'^pi_[A-Za-z0-9]{24,}$',     # Stripe
            r'^[0-9]{17,20}$',            # PayPal transaction
            r'^TXN[0-9]{10,}$',           # Generic transaction
        ]
        
        return any(re.match(pattern, payment_id) for pattern in patterns)
    
    def _validate_date_consistency(self, feedback: VerifiedFeedback) -> bool:
        """Check if dates make logical sense"""
        if not feedback.order_date:
            return False
        
        # Order date should be in the past
        if feedback.order_date > datetime.utcnow():
            return False
        
        # If delivered, delivery date should be after order date
        if feedback.actual_delivery and feedback.order_date:
            if feedback.actual_delivery < feedback.order_date:
                return False
        
        # Order shouldn't be more than 1 year old for feedback
        days_since_order = (datetime.utcnow() - feedback.order_date).days
        if days_since_order > 365:
            return False
        
        return True
    
    async def verify_proof_files(self, proofs: List[VerificationProof]) -> float:
        """Verify uploaded proof files"""
        score = 0.0
        proof_types_found = set()
        
        for proof in proofs:
            proof_types_found.add(proof.proof_type)
            
            # Basic file validation
            if self._validate_file_hash(proof.file_hash):
                score += 10.0
            
            # Metadata validation
            if self._validate_proof_metadata(proof):
                score += 15.0
            
            # Specific proof type validation
            type_score = await self._validate_specific_proof_type(proof)
            score += type_score
        
        # Bonus for having multiple proof types
        if len(proof_types_found) >= 3:
            score += 20.0
        elif len(proof_types_found) >= 2:
            score += 10.0
        
        return min(100.0, score)
    
    def _validate_file_hash(self, file_hash: str) -> bool:
        """Validate file hash format and uniqueness"""
        # Check SHA-256 format
        if not re.match(r'^[a-f0-9]{64}$', file_hash):
            return False
        
        # TODO: Check against database for uniqueness
        # Prevent same proof being used multiple times
        
        return True
    
    def _validate_proof_metadata(self, proof: VerificationProof) -> bool:
        """Validate proof metadata makes sense"""
        metadata = proof.metadata
        
        # Check required metadata fields
        required_fields = ['timestamp', 'file_size', 'file_type']
        if not all(field in metadata for field in required_fields):
            return False
        
        # Validate timestamp (should be recent for delivery notifications)
        if proof.proof_type == ProofType.DELIVERY_NOTIFICATION:
            timestamp = metadata.get('timestamp')
            if timestamp:
                # Should be within last 90 days
                import time
                if time.time() - timestamp > 90 * 24 * 3600:
                    return False
        
        return True
    
    async def _validate_specific_proof_type(self, proof: VerificationProof) -> float:
        """Validate specific proof types with OCR/analysis"""
        # This would integrate with OCR services to extract text from images
        # and validate specific content
        
        validation_scores = {
            ProofType.ORDER_SCREENSHOT: 25.0,
            ProofType.DELIVERY_NOTIFICATION: 30.0,
            ProofType.PAYMENT_RECEIPT: 25.0,
            ProofType.BANK_STATEMENT: 20.0,
            ProofType.EMAIL_CONFIRMATION: 15.0,
            ProofType.TRACKING_INFO: 20.0
        }
        
        base_score = validation_scores.get(proof.proof_type, 10.0)
        
        # TODO: Implement actual OCR validation
        # - Extract order IDs from screenshots
        # - Validate delivery addresses
        # - Check payment amounts
        # - Verify merchant names
        
        return base_score
    
    async def calculate_final_verification_score(
        self, 
        feedback: VerifiedFeedback, 
        proofs: List[VerificationProof]
    ) -> tuple[float, FeedbackStatus]:
        """Calculate final verification score and status"""
        
        order_score = await self.verify_order_details(feedback)
        proof_score = await self.verify_proof_files(proofs)
        
        # Weighted average
        final_score = (order_score * 0.4) + (proof_score * 0.6)
        
        # Determine status based on score
        if final_score >= 85.0:
            if feedback.delivered_successfully:
                status = FeedbackStatus.VERIFIED_DELIVERED
            else:
                status = FeedbackStatus.VERIFIED_SCAM
        elif final_score >= 60.0:
            status = FeedbackStatus.PENDING_VERIFICATION
        else:
            status = FeedbackStatus.VERIFICATION_FAILED
        
        return final_score, status
    
    def calculate_feedback_weight(self, verification_score: float, user_history: Dict) -> float:
        """Calculate how much weight this feedback should have"""
        base_weight = verification_score / 100.0
        
        # User reputation multiplier
        user_reputation = user_history.get('reputation', 50.0)
        reputation_multiplier = min(2.0, user_reputation / 50.0)
        
        # Recency bonus (recent feedback matters more)
        recency_bonus = 1.0  # TODO: Calculate based on submission date
        
        final_weight = base_weight * reputation_multiplier * recency_bonus
        
        return min(1.0, final_weight)

# API Integration
class VerifiedFeedbackAPI:
    """API endpoints for verified feedback system"""
    
    def __init__(self):
        self.verifier = FeedbackVerifier()
    
    async def submit_feedback(
        self, 
        url: str, 
        user_id: str, 
        order_details: Dict, 
        proof_files: List[Dict],
        outcome: Dict
    ) -> Dict:
        """Submit new verified feedback"""
        
        # Create feedback record
        feedback = VerifiedFeedback(
            url=url,
            user_id=user_id,
            order_id=order_details.get('order_id'),
            payment_id=order_details.get('payment_id'),
            order_amount=order_details.get('amount'),
            order_date=order_details.get('order_date'),
            product_name=order_details.get('product_name'),
            delivered_successfully=outcome.get('delivered'),
            delivery_quality=outcome.get('quality'),
            payment_issues=outcome.get('payment_issues', False)
        )
        
        # Process proof files
        proofs = []
        for proof_file in proof_files:
            proof = VerificationProof(
                proof_type=ProofType(proof_file['type']),
                file_hash=proof_file['hash'],
                metadata=proof_file['metadata'],
                confidence_score=0.0
            )
            proofs.append(proof)
        
        # Verify and score
        verification_score, status = await self.verifier.calculate_final_verification_score(
            feedback, proofs
        )
        
        feedback.verification_score = verification_score
        feedback.status = status
        
        # Calculate weight for risk score impact
        user_history = {}  # TODO: Get from database
        feedback.weight = self.verifier.calculate_feedback_weight(
            verification_score, user_history
        )
        
        return {
            "feedback_id": feedback.id,
            "status": status,
            "verification_score": verification_score,
            "weight": feedback.weight,
            "message": self._get_status_message(status)
        }
    
    def _get_status_message(self, status: FeedbackStatus) -> str:
        messages = {
            FeedbackStatus.PENDING_VERIFICATION: "Thank you for your feedback. We're verifying your proof documents.",
            FeedbackStatus.VERIFIED_DELIVERED: "Feedback verified successfully. This will improve our risk assessment.",
            FeedbackStatus.VERIFIED_SCAM: "Scam report verified. Other users will be warned about this site.",
            FeedbackStatus.VERIFICATION_FAILED: "Unable to verify your feedback. Please check your proof documents.",
            FeedbackStatus.REJECTED: "Feedback rejected due to insufficient or invalid proof."
        }
        return messages.get(status, "Unknown status")