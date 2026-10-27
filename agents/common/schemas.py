from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class IssueCategory(str, Enum):
    POTHOLE = "pothole"
    GARBAGE = "garbage"
    STREETLIGHT = "streetlight"
    WATER_LEAKAGE = "water_leakage"
    DRAINAGE = "drainage"
    FOOTPATH = "footpath"
    OBSTRUCTION = "obstruction"
    PROPERTY_DAMAGE = "property_damage"
    SANITATION = "sanitation"
    OTHER = "other"


class PriorityBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    SAFETY_ESCALATION = "safety_escalation"


class AgentMessageBase(BaseModel):
    message_id: UUID
    correlation_id: UUID
    schema_version: str = "1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str


class ClassificationRequest(AgentMessageBase):
    report_id: UUID
    description: str
    image_urls: List[str] = []
    category_hint: Optional[IssueCategory] = None


class ClassificationResponse(AgentMessageBase):
    report_id: UUID
    predicted_category: IssueCategory
    confidence: float
    alternatives: List[Dict[str, Any]] = []
    explanation: str
    evidence_quality: str
    needs_human_review: bool
    model_version: str
    is_mock: bool = False


class VerificationRequest(AgentMessageBase):
    report_id: UUID
    title: Optional[str] = None
    description: str
    category: IssueCategory
    category_confidence: Optional[float] = None
    media_metadata: List[Dict[str, Any]] = []


class VerificationResponse(AgentMessageBase):
    report_id: UUID
    status: str
    missing_fields: List[str] = []
    evidence_quality: str
    review_recommendation: str
    issues: List[str] = []


class DuplicateRequest(AgentMessageBase):
    report_id: UUID
    coordinates: Dict[str, float]
    category: IssueCategory
    description: str
    image_features: Optional[Dict[str, Any]] = None
    radius_override: Optional[int] = None


class DuplicateCandidate(BaseModel):
    candidate_report_id: UUID
    candidate_tracking_id: str
    candidate_category: IssueCategory
    distance_meters: float
    category_match: bool
    description_similarity: float
    image_similarity: Optional[float] = None
    time_proximity_hours: float
    match_score: float
    match_explanation: str
    suggested_action: str


class DuplicateResponse(AgentMessageBase):
    report_id: UUID
    candidates: List[DuplicateCandidate] = []


class PriorityRequest(AgentMessageBase):
    report_id: UUID
    category: IssueCategory
    severity_indicators: Dict[str, Any] = {}
    risk_indicators: Dict[str, Any] = {}
    created_at: datetime
    duplicate_count: int = 0
    rule_version: str = "v1.0"


class PriorityResponse(AgentMessageBase):
    report_id: UUID
    priority_score: float
    priority_band: PriorityBand
    severity_score: float
    risk_score: float
    time_score: float
    corroboration_score: float
    factor_details: Dict[str, Any]
    escalation_recommended: bool
    escalation_reason: Optional[str] = None
    rule_version: str


class RoutingRequest(AgentMessageBase):
    report_id: UUID
    category: IssueCategory
    coordinates: Dict[str, float]
    priority_band: PriorityBand
    service_zone_id: Optional[UUID] = None


class RoutingResponse(AgentMessageBase):
    report_id: UUID
    department_id: UUID
    department_name: str
    queue: str
    reason: str
    needs_manual_review: bool


class MonitoringRequest(AgentMessageBase):
    report_id: UUID
    status: str
    priority_band: PriorityBand
    assigned_department_id: Optional[UUID] = None
    sla_deadline: Optional[datetime] = None
    last_update: datetime


class MonitoringResponse(AgentMessageBase):
    report_id: UUID
    overdue: bool
    escalation_recommended: bool
    escalation_reason: Optional[str] = None
    notification_event: Optional[str] = None


class AgentErrorResponse(AgentMessageBase):
    report_id: UUID
    error_code: str
    error_message: str
    retryable: bool = False