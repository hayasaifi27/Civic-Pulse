from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from pydantic.types import conint, confloat


class UserRole(str, Enum):
    CITIZEN = "citizen"
    ADMIN = "admin"
    FIELD_WORKER = "field_worker"
    SUPERVISOR = "supervisor"


class ReportStatus(str, Enum):
    REPORTED = "reported"
    UNDER_REVIEW = "under_review"
    NEEDS_MORE_INFO = "needs_more_info"
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED_PENDING_CONFIRMATION = "resolved_pending_confirmation"
    CLOSED = "closed"
    REJECTED = "rejected"
    REOPENED = "reopened"


class PriorityBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    SAFETY_ESCALATION = "safety_escalation"


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


class DuplicateStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    UNLINKED = "unlinked"


class AssignmentStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class ResolutionStatus(str, Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REWORK = "needs_rework"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class Coordinates(BaseModel):
    latitude: confloat(ge=-90, le=90)
    longitude: confloat(ge=-180, le=180)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    sub: Optional[str] = None
    role: Optional[UserRole] = None


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    department_id: Optional[UUID] = None
    service_zone_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserWithToken(UserResponse):
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class CategoryBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    severity_base: conint(ge=0, le=100) = 50
    risk_base: conint(ge=0, le=100) = 50
    department_id: Optional[UUID] = None
    sla_hours: conint(ge=1) = 72
    duplicate_distance_meters: conint(ge=1) = 100
    is_active: bool = True
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    severity_base: Optional[conint(ge=0, le=100)] = None
    risk_base: Optional[conint(ge=0, le=100)] = None
    department_id: Optional[UUID] = None
    sla_hours: Optional[conint(ge=1)] = None
    duplicate_distance_meters: Optional[conint(ge=1)] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    sla_hours: conint(ge=1) = 72


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    sla_hours: Optional[conint(ge=1)] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServiceZoneBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    boundary: Dict[str, Any]
    description: Optional[str] = None


class ServiceZoneCreate(ServiceZoneBase):
    pass


class ServiceZoneResponse(ServiceZoneBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoutingRuleBase(BaseModel):
    category_id: UUID
    department_id: UUID
    service_zone_id: Optional[UUID] = None
    priority_band: Optional[PriorityBand] = None
    is_default: bool = False


class RoutingRuleCreate(RoutingRuleBase):
    pass


class RoutingRuleResponse(RoutingRuleBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MediaUploadResponse(BaseModel):
    id: UUID
    storage_path: str
    file_name: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    upload_url: Optional[str] = None


class ReportMediaResponse(BaseModel):
    id: UUID
    storage_path: str
    file_name: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    is_primary: bool
    sort_order: int
    analysis_result: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: str = Field(..., min_length=10, max_length=5000)
    category: IssueCategory
    coordinates: Coordinates
    address: Optional[str] = Field(None, max_length=500)
    landmark: Optional[str] = Field(None, max_length=500)
    is_anonymous: bool = False


class ReportCreate(ReportBase):
    media_ids: List[UUID] = Field(default_factory=list)


class ReportUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    category: Optional[IssueCategory] = None
    coordinates: Optional[Coordinates] = None
    address: Optional[str] = Field(None, max_length=500)
    landmark: Optional[str] = Field(None, max_length=500)
    is_anonymous: Optional[bool] = None
    is_public: Optional[bool] = None


class ReportStatusUpdate(BaseModel):
    status: ReportStatus
    reason: Optional[str] = None


class ReportAssign(BaseModel):
    department_id: UUID
    worker_id: Optional[UUID] = None
    instructions: Optional[str] = None
    sla_deadline: Optional[datetime] = None


class ReportResponse(BaseModel):
    id: UUID
    tracking_id: str
    title: Optional[str]
    description: str
    category: IssueCategory
    category_confidence: Optional[float] = None
    category_source: Optional[str] = None
    coordinates: Coordinates
    address: Optional[str] = None
    landmark: Optional[str] = None
    status: ReportStatus
    priority_score: float
    priority_band: PriorityBand
    priority_version: Optional[str] = None
    assigned_department_id: Optional[UUID] = None
    reporter_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    is_anonymous: bool
    is_public: bool
    duplicate_primary_id: Optional[UUID] = None
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    media: List[ReportMediaResponse] = []
    assigned_department: Optional[DepartmentResponse] = None

    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    id: UUID
    tracking_id: str
    title: Optional[str]
    description: str
    category: IssueCategory
    coordinates: Coordinates
    address: Optional[str] = None
    status: ReportStatus
    priority_score: float
    priority_band: PriorityBand
    created_at: datetime
    updated_at: datetime
    media_count: int = 0
    primary_media: Optional[ReportMediaResponse] = None

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReportEventResponse(BaseModel):
    id: UUID
    event_type: str
    previous_status: Optional[ReportStatus] = None
    new_status: Optional[ReportStatus] = None
    actor_id: Optional[UUID] = None
    actor_role: Optional[UserRole] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportCommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = False


class ReportCommentCreate(ReportCommentBase):
    pass


class ReportCommentResponse(ReportCommentBase):
    id: UUID
    report_id: UUID
    author_id: UUID
    author_name: Optional[str] = None
    author_role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DuplicateCandidateResponse(BaseModel):
    id: UUID
    report_id: UUID
    candidate_report_id: UUID
    candidate_tracking_id: str
    candidate_title: Optional[str]
    candidate_category: IssueCategory
    candidate_coordinates: Coordinates
    candidate_status: ReportStatus
    distance_meters: Optional[float] = None
    category_match: bool
    description_similarity: Optional[float] = None
    image_similarity: Optional[float] = None
    time_proximity_hours: Optional[float] = None
    match_score: float
    match_explanation: str
    suggested_action: str
    status: DuplicateStatus
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DuplicateReviewRequest(BaseModel):
    action: str = Field(..., pattern="^(confirm|reject|unlink)$")
    reason: Optional[str] = None


class AssignmentResponse(BaseModel):
    id: UUID
    report_id: UUID
    department_id: UUID
    worker_id: Optional[UUID] = None
    assigned_by: Optional[UUID] = None
    status: AssignmentStatus
    priority: int
    instructions: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    department: Optional[DepartmentResponse] = None
    worker: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class ResolutionEvidenceBase(BaseModel):
    before_media: Optional[List[Dict[str, Any]]] = None
    after_media: Optional[List[Dict[str, Any]]] = None
    work_notes: Optional[str] = None


class ResolutionEvidenceCreate(ResolutionEvidenceBase):
    assignment_id: Optional[UUID] = None


class ResolutionEvidenceResponse(ResolutionEvidenceBase):
    id: UUID
    report_id: UUID
    assignment_id: Optional[UUID] = None
    submitted_by_id: UUID
    status: ResolutionStatus
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_by: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class ResolutionReviewRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|needs_rework)$")
    notes: Optional[str] = None


class PriorityAssessmentResponse(BaseModel):
    id: UUID
    report_id: UUID
    severity_score: float
    risk_score: float
    time_score: float
    corroboration_score: float
    total_score: float
    priority_band: PriorityBand
    rule_version: str
    factor_details: Dict[str, Any]
    escalation_recommended: bool
    escalation_reason: Optional[str] = None
    assessed_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class AgentRunResponse(BaseModel):
    id: UUID
    report_id: UUID
    agent_type: str
    agent_version: Optional[str] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    correlation_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClassificationResult(BaseModel):
    predicted_category: IssueCategory
    confidence: confloat(ge=0, le=1)
    alternatives: List[Dict[str, Any]] = []
    explanation: str
    evidence_quality: str = Field(..., pattern="^(good|fair|poor)$")
    needs_human_review: bool
    model_version: str
    is_mock: bool = False


class VerificationResult(BaseModel):
    status: str = Field(..., pattern="^(valid|needs_info|needs_review|rejected)$")
    missing_fields: List[str] = []
    evidence_quality: str = Field(..., pattern="^(good|fair|poor)$")
    review_recommendation: str
    issues: List[str] = []


class PriorityScoreResult(BaseModel):
    priority_score: confloat(ge=0, le=100)
    priority_band: PriorityBand
    severity_score: confloat(ge=0, le=100)
    risk_score: confloat(ge=0, le=100)
    time_score: confloat(ge=0, le=100)
    corroboration_score: confloat(ge=0, le=100)
    factor_details: Dict[str, Any]
    escalation_recommended: bool
    escalation_reason: Optional[str] = None
    rule_version: str


class RoutingRecommendation(BaseModel):
    department_id: UUID
    department_name: str
    queue: str
    reason: str
    needs_manual_review: bool


class NotificationResponse(BaseModel):
    id: UUID
    report_id: Optional[UUID] = None
    channel: NotificationChannel
    event_type: str
    title: str
    message: str
    data: Dict[str, Any]
    is_read: bool
    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsOverview(BaseModel):
    total_reports: int
    reports_awaiting_review: int
    active_assignments: int
    overdue_issues: int
    resolved_closed: int
    median_time_to_acknowledgment_hours: Optional[float] = None
    median_time_to_resolution_hours: Optional[float] = None
    resolution_rate: float
    reopened_rate: float


class CategoryDistribution(BaseModel):
    category: IssueCategory
    count: int
    percentage: float


class DepartmentWorkload(BaseModel):
    department_id: UUID
    department_name: str
    assigned: int
    in_progress: int
    completed: int
    overdue: int
    avg_resolution_hours: Optional[float] = None


class HotspotData(BaseModel):
    coordinates: Coordinates
    count: int
    categories: List[IssueCategory]
    avg_priority: float
    radius_meters: int


class TimeSeriesPoint(BaseModel):
    date: str
    count: int


class TimeSeriesData(BaseModel):
    series: List[TimeSeriesPoint]
    granularity: str


class ScoringRuleBase(BaseModel):
    version: str = Field(..., min_length=1, max_length=50)
    severity_weight: confloat(ge=0, le=1) = 0.35
    risk_weight: confloat(ge=0, le=1) = 0.25
    time_weight: confloat(ge=0, le=1) = 0.20
    corroboration_weight: confloat(ge=0, le=1) = 0.20
    safety_escalation_threshold: confloat(ge=0, le=100) = 85.0
    is_active: bool = True
    description: Optional[str] = None


class ScoringRuleCreate(ScoringRuleBase):
    pass


class ScoringRuleResponse(ScoringRuleBase):
    id: UUID
    created_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class HealthCheck(BaseModel):
    status: str
    version: str
    database: str
    agents: Dict[str, str]
    demo_mode: bool


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    error: str = "validation_error"
    message: str
    details: List[Dict[str, Any]]