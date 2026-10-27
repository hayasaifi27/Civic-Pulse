from typing import Type, TypeVar, Generic
from pydantic import BaseModel
from uagents import Model


T = TypeVar('T', bound=BaseModel)


class UAgentMessage(Model):
    pass


class ClassificationRequest(UAgentMessage):
    report_id: str
    description: str
    image_urls: list[str] = []
    category_hint: str | None = None
    correlation_id: str
    message_id: str


class ClassificationResponse(UAgentMessage):
    report_id: str
    predicted_category: str
    confidence: float
    alternatives: list[dict] = []
    explanation: str
    evidence_quality: str
    needs_human_review: bool
    model_version: str
    is_mock: bool = False
    correlation_id: str
    message_id: str


class DuplicateRequest(UAgentMessage):
    report_id: str
    latitude: float
    longitude: float
    category: str
    description: str
    image_features: dict | None = None
    radius_override: int | None = None
    correlation_id: str
    message_id: str


class DuplicateCandidate(UAgentMessage):
    candidate_report_id: str
    candidate_tracking_id: str
    candidate_category: str
    distance_meters: float
    category_match: bool
    description_similarity: float
    image_similarity: float | None = None
    time_proximity_hours: float
    match_score: float
    match_explanation: str
    suggested_action: str


class DuplicateResponse(UAgentMessage):
    report_id: str
    candidates: list[DuplicateCandidate] = []
    correlation_id: str
    message_id: str


class PriorityRequest(UAgentMessage):
    report_id: str
    category: str
    severity_indicators: dict = {}
    risk_indicators: dict = {}
    created_at: str
    duplicate_count: int = 0
    rule_version: str = "v1.0"
    correlation_id: str
    message_id: str


class PriorityResponse(UAgentMessage):
    report_id: str
    priority_score: float
    priority_band: str
    severity_score: float
    risk_score: float
    time_score: float
    corroboration_score: float
    factor_details: dict
    escalation_recommended: bool
    escalation_reason: str | None = None
    rule_version: str
    correlation_id: str
    message_id: str


class RoutingRequest(UAgentMessage):
    report_id: str
    category: str
    latitude: float
    longitude: float
    priority_band: str
    service_zone_id: str | None = None
    correlation_id: str
    message_id: str


class RoutingResponse(UAgentMessage):
    report_id: str
    department_id: str
    department_name: str
    queue: str
    reason: str
    needs_manual_review: bool
    correlation_id: str
    message_id: str


class MonitoringRequest(UAgentMessage):
    report_id: str
    status: str
    priority_band: str
    assigned_department_id: str | None = None
    sla_deadline: str | None = None
    last_update: str
    correlation_id: str
    message_id: str


class MonitoringResponse(UAgentMessage):
    report_id: str
    overdue: bool
    escalation_recommended: bool
    escalation_reason: str | None = None
    notification_event: str | None = None
    correlation_id: str
    message_id: str


class AgentErrorResponse(UAgentMessage):
    report_id: str
    error_code: str
    error_message: str
    retryable: bool = False
    correlation_id: str
    message_id: str