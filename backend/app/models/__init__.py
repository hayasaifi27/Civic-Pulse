import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum, Integer, Float, Boolean,
    Index, UniqueConstraint, CheckConstraint, func, UUID as SQLUUID
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship, declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()


class UserRole(str, PyEnum):
    CITIZEN = "citizen"
    ADMIN = "admin"
    FIELD_WORKER = "field_worker"
    SUPERVISOR = "supervisor"


class ReportStatus(str, PyEnum):
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


class PriorityBand(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    SAFETY_ESCALATION = "safety_escalation"


class IssueCategory(str, PyEnum):
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


class DuplicateStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    UNLINKED = "unlinked"


class AssignmentStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class ResolutionStatus(str, PyEnum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REWORK = "needs_rework"


class NotificationChannel(str, PyEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    phone = Column(String(50))
    avatar_url = Column(String(500))
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CITIZEN, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    department_id = Column(SQLUUID(as_uuid=True), ForeignKey("departments.id"))
    service_zone_id = Column(SQLUUID(as_uuid=True), ForeignKey("service_zones.id"))
    preferences = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    reports = relationship("Report", back_populates="reporter", foreign_keys="Report.reporter_id")
    assigned_reports = relationship("Report", back_populates="assignee", foreign_keys="Report.assignee_id")
    comments = relationship("ReportComment", back_populates="author")
    assignments = relationship("Assignment", back_populates="worker", foreign_keys="Assignment.worker_id")
    resolutions = relationship("ResolutionEvidence", back_populates="submitted_by", foreign_keys="ResolutionEvidence.submitted_by_id")
    notifications = relationship("Notification", back_populates="user")
    service_zone = relationship("ServiceZone", back_populates="profiles")


class Department(Base):
    __tablename__ = "departments"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    sla_hours = Column(Integer, default=72)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    routing_rules = relationship("RoutingRule", back_populates="department")
    assignments = relationship("Assignment", back_populates="department")


class ServiceZone(Base):
    __tablename__ = "service_zones"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    # Store GeoJSON as text (works with both SQLite and PostgreSQL)
    boundary = Column(Text, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    profiles = relationship("Profile", back_populates="service_zone")
    routing_rules = relationship("RoutingRule", back_populates="service_zone")


class ConfigurableCategory(Base):
    __tablename__ = "configurable_categories"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    color = Column(String(7))
    severity_base = Column(Integer, default=50)
    risk_base = Column(Integer, default=50)
    department_id = Column(SQLUUID(as_uuid=True), ForeignKey("departments.id"))
    sla_hours = Column(Integer, default=72)
    duplicate_distance_meters = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    department = relationship("Department")


class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(SQLUUID(as_uuid=True), ForeignKey("configurable_categories.id"), nullable=False)
    department_id = Column(SQLUUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    service_zone_id = Column(SQLUUID(as_uuid=True), ForeignKey("service_zones.id"))
    priority_band = Column(Enum(PriorityBand))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("ConfigurableCategory")
    department = relationship("Department", back_populates="routing_rules")
    service_zone = relationship("ServiceZone", back_populates="routing_rules")


class Report(Base):
    __tablename__ = "reports"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(500))
    description = Column(Text, nullable=False)
    category = Column(Enum(IssueCategory), nullable=False, index=True)
    category_confidence = Column(Float)
    category_source = Column(String(50))
    # Store coordinates as GeoJSON text (works with both SQLite and PostgreSQL)
    coordinates = Column(Text, nullable=False, index=True)
    address = Column(String(500))
    landmark = Column(String(500))
    status = Column(Enum(ReportStatus), default=ReportStatus.REPORTED, nullable=False, index=True)
    priority_score = Column(Float, default=0.0)
    priority_band = Column(Enum(PriorityBand), default=PriorityBand.LOW, index=True)
    priority_version = Column(String(50))
    assigned_department_id = Column(SQLUUID(as_uuid=True), ForeignKey("departments.id"), index=True)
    reporter_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"), index=True)
    assignee_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"), index=True)
    is_anonymous = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    duplicate_primary_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id"), index=True)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    verified_at = Column(DateTime(timezone=True))
    assigned_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))

    reporter = relationship("Profile", back_populates="reports", foreign_keys=[reporter_id])
    assignee = relationship("Profile", back_populates="assigned_reports", foreign_keys=[assignee_id])
    assigned_department = relationship("Department")
    media = relationship("ReportMedia", back_populates="report", cascade="all, delete-orphan")
    events = relationship("ReportEvent", back_populates="report", cascade="all, delete-orphan")
    comments = relationship("ReportComment", back_populates="report", cascade="all, delete-orphan")
    duplicate_candidates = relationship("DuplicateCandidate", back_populates="report", foreign_keys="DuplicateCandidate.report_id", cascade="all, delete-orphan")
    linked_duplicates = relationship("ReportLink", back_populates="primary_report", foreign_keys="ReportLink.primary_report_id", cascade="all, delete-orphan")
    linked_as_duplicate = relationship("ReportLink", back_populates="duplicate_report", foreign_keys="ReportLink.duplicate_report_id", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="report", cascade="all, delete-orphan")
    resolution_evidence = relationship("ResolutionEvidence", back_populates="report", cascade="all, delete-orphan")
    priority_assessments = relationship("PriorityAssessment", back_populates="report", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_reports_category_status", "category", "status"),
        Index("ix_reports_created_status", "created_at", "status"),
        Index("ix_reports_coords_status", "coordinates", "status"),
    )


class ReportMedia(Base):
    __tablename__ = "report_media"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_path = Column(String(500), nullable=False)
    file_name = Column(String(255))
    mime_type = Column(String(100))
    file_size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    analysis_result = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    report = relationship("Report", back_populates="media")


class ReportEvent(Base):
    __tablename__ = "report_events"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    previous_status = Column(Enum(ReportStatus))
    new_status = Column(Enum(ReportStatus))
    actor_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    actor_role = Column(Enum(UserRole))
    reason = Column(Text)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    report = relationship("Report", back_populates="events")


class ReportComment(Base):
    __tablename__ = "report_comments"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    report = relationship("Report", back_populates="comments")
    author = relationship("Profile", back_populates="comments")


class DuplicateCandidate(Base):
    __tablename__ = "duplicate_candidates"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    distance_meters = Column(Float)
    category_match = Column(Boolean)
    description_similarity = Column(Float)
    image_similarity = Column(Float)
    time_proximity_hours = Column(Float)
    match_score = Column(Float)
    match_explanation = Column(Text)
    suggested_action = Column(String(50))
    status = Column(Enum(DuplicateStatus), default=DuplicateStatus.PENDING)
    reviewed_by = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    reviewed_at = Column(DateTime(timezone=True))
    review_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    report = relationship("Report", back_populates="duplicate_candidates", foreign_keys=[report_id])
    candidate_report = relationship("Report", foreign_keys=[candidate_report_id])


class ReportLink(Base):
    __tablename__ = "report_links"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primary_report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    duplicate_report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    linked_by = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    link_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    primary_report = relationship("Report", back_populates="linked_duplicates", foreign_keys=[primary_report_id])
    duplicate_report = relationship("Report", back_populates="linked_as_duplicate", foreign_keys=[duplicate_report_id])

    __table_args__ = (
        UniqueConstraint("primary_report_id", "duplicate_report_id", name="uq_report_link"),
    )


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(SQLUUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    worker_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"), index=True)
    assigned_by = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.PENDING, index=True)
    priority = Column(Integer, default=0)
    instructions = Column(Text)
    sla_deadline = Column(DateTime(timezone=True))
    accepted_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    report = relationship("Report", back_populates="assignments")
    department = relationship("Department", back_populates="assignments")
    worker = relationship("Profile", back_populates="assignments", foreign_keys="Assignment.worker_id")


class ResolutionEvidence(Base):
    __tablename__ = "resolution_evidence"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = Column(SQLUUID(as_uuid=True), ForeignKey("assignments.id"))
    submitted_by_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    before_media = Column(JSONB)
    after_media = Column(JSONB)
    work_notes = Column(Text)
    status = Column(Enum(ResolutionStatus), default=ResolutionStatus.SUBMITTED, index=True)
    reviewed_by = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    report = relationship("Report", back_populates="resolution_evidence")
    submitted_by = relationship("Profile", back_populates="resolutions", foreign_keys="ResolutionEvidence.submitted_by_id")


class PriorityAssessment(Base):
    __tablename__ = "priority_assessments"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    severity_score = Column(Float)
    risk_score = Column(Float)
    time_score = Column(Float)
    corroboration_score = Column(Float)
    total_score = Column(Float)
    priority_band = Column(Enum(PriorityBand))
    rule_version = Column(String(50))
    factor_details = Column(JSONB)
    escalation_recommended = Column(Boolean, default=False)
    escalation_reason = Column(Text)
    assessed_by = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    report = relationship("Report", back_populates="priority_assessments")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)
    agent_version = Column(String(50))
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    status = Column(String(50))
    error_message = Column(Text)
    duration_ms = Column(Integer)
    correlation_id = Column(String(100), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    report = relationship("Report", back_populates="agent_runs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False, index=True)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id"))
    channel = Column(Enum(NotificationChannel), default=NotificationChannel.IN_APP)
    event_type = Column(String(100), nullable=False)
    title = Column(String(255))
    message = Column(Text)
    data = Column(JSONB, default={})
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("Profile", back_populates="notifications")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    rating = Column(Integer)
    comment = Column(Text)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    actor_role = Column(Enum(UserRole))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(SQLUUID(as_uuid=True))
    previous_state = Column(JSONB)
    new_state = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_actor_created", "actor_id", "created_at"),
    )


class ModerationAction(Base):
    __tablename__ = "moderation_actions"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    target_user_id = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    target_report_id = Column(SQLUUID(as_uuid=True), ForeignKey("reports.id"))
    action_type = Column(String(50))
    reason = Column(Text)
    duration_days = Column(Integer)
    created_by = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))


class ScoringRule(Base):
    __tablename__ = "scoring_rules"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(50), unique=True, nullable=False)
    severity_weight = Column(Float, default=0.35)
    risk_weight = Column(Float, default=0.25)
    time_weight = Column(Float, default=0.20)
    corroboration_weight = Column(Float, default=0.20)
    safety_escalation_threshold = Column(Float, default=85.0)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(SQLUUID(as_uuid=True), ForeignKey("profiles.id"))