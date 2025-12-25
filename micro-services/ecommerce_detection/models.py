from __future__ import annotations
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Request Models
class EcommerceAnalysisRequest(BaseModel):
    """Request model for advanced e-commerce analysis."""
    url: HttpUrl

class FeedbackRequest(BaseModel):
    """Request model for submitting feedback about a site."""
    url: HttpUrl
    delivered: bool
    order_hash: Optional[str] = Field(default=None, description="Optional proof hash or reference ID")

# Response Models
class Reason(BaseModel):
    """Individual reason from analysis layer."""
    layer: str
    message: str
    weight: float
    score: float

class Advice(BaseModel):
    """Advice for users based on risk score."""
    payment: str
    actions: List[str]

class MerchantInfo(BaseModel):
    """Merchant verification information."""
    platform: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    verification_status: str = "unknown"
    trust_score: float = 0.0
    verification_badges: List[str] = []

class BusinessVerification(BaseModel):
    """Business verification details."""
    is_registered: bool = False
    gst_valid: bool = False
    linkedin_verified: bool = False
    phone_verified: bool = False
    address_verified: bool = False

class AdvancedEcommerceResult(BaseModel):
    """Advanced e-commerce analysis result."""
    url: HttpUrl
    risk_score: float = Field(ge=0, le=100)
    badge: str
    reasons: List[Reason]
    advice: Advice
    scanned_at: datetime
    merchant_info: Optional[MerchantInfo] = None
    business_verification: Optional[BusinessVerification] = None

# History Models
class HistoryPoint(BaseModel):
    """Point in time for site history."""
    scanned_at: datetime
    risk_score: float
    badge: str

class SiteHistoryResponse(BaseModel):
    """Site history response."""
    url: HttpUrl
    timeline: List[HistoryPoint]

# Status Models
class AnalysisStatus(BaseModel):
    """Status of analysis operation."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
