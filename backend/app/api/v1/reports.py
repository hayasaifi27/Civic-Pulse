import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user, require_admin, require_staff, require_field_worker, require_supervisor
from app.repositories import (
    ReportRepository, ReportMediaRepository, ReportEventRepository,
    DuplicateRepository, AssignmentRepository, ResolutionRepository,
    PriorityRepository, CategoryRepository, DepartmentRepository,
    NotificationRepository, AuditRepository
)
from app.services.intelligence import (
    ClassificationService, VerificationService, DuplicateDetectionService,
    PriorityScoringService, RoutingService
)
from app.schemas import (
    ReportCreate, ReportUpdate, ReportResponse, ReportListItem,
    ReportStatusUpdate, ReportAssign, ReportCommentCreate, ReportCommentResponse,
    DuplicateCandidateResponse, DuplicateReviewRequest,
    AssignmentResponse, ResolutionEvidenceCreate, ResolutionEvidenceResponse,
    ResolutionReviewRequest, PriorityAssessmentResponse,
    PaginatedResponse, Coordinates, ReportStatus, IssueCategory,
    PriorityBand, UserRole, NotificationChannel
)
from app.models import Report, ReportMedia, ReportEvent, ReportComment, ReportStatus as ReportStatusEnum
from app.services.storage import StorageService

router = APIRouter(prefix="/reports", tags=["Reports"])


def generate_tracking_id() -> str:
    import random
    import string
    return "CP" + "".join(random.choices(string.digits, k=8))


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    current_user: Optional[Profile] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models import Profile
    report_repo = ReportRepository(db)
    media_repo = ReportMediaRepository(db)
    event_repo = ReportEventRepository(db)
    audit_repo = AuditRepository(db)
    cat_repo = CategoryRepository(db)
    classification_service = ClassificationService()
    verification_service = VerificationService()
    duplicate_service = DuplicateDetectionService(db)
    priority_service = PriorityScoringService(db)
    routing_service = RoutingService(db)
    notification_repo = NotificationRepository(db)
    
    category_config = await cat_repo.get_by_code(report_data.category.value)
    
    report = Report(
        tracking_id=generate_tracking_id(),
        title=report_data.title,
        description=report_data.description,
        category=report_data.category,
        coordinates=f"POINT({report_data.coordinates.longitude} {report_data.coordinates.latitude})",
        address=report_data.address,
        landmark=report_data.landmark,
        reporter_id=current_user.id if current_user else None,
        is_anonymous=report_data.is_anonymous,
        status=ReportStatusEnum.REPORTED,
        metadata={"source": "api"}
    )
    
    await report_repo.create(report)
    
    media_list = []
    for media_id in report_data.media_ids:
        media = await media_repo.get_by_id(media_id)
        if media and media.report_id is None:
            media.report_id = report.id
            media_list.append(media)
    
    await db.flush()
    
    media_urls = [f"/api/v1/media/{m.storage_path}" for m in media_list]
    
    classification = await classification_service.classify_report(report, media_urls)
    report.category_confidence = classification.confidence
    report.category_source = "ai" if not classification.is_mock else "mock"
    
    if report.category != classification.predicted_category and classification.confidence > 0.7:
        report.metadata["ai_suggested_category"] = classification.predicted_category.value
    
    verification = await verification_service.verify_report(report, [{"file_size": m.file_size, "mime_type": m.mime_type, "file_name": m.file_name} for m in media_list], classification)
    
    if verification.status == "needs_info":
        report.status = ReportStatusEnum.NEEDS_MORE_INFO
    elif verification.status in ["needs_review", "rejected"]:
        report.status = ReportStatusEnum.UNDER_REVIEW
    else:
        report.status = ReportStatusEnum.UNDER_REVIEW
    
    candidates = await duplicate_service.find_candidates(report)
    duplicate_count = len(candidates)
    
    for cand in candidates:
        from app.models import DuplicateCandidate
        dup_cand = DuplicateCandidate(
            report_id=report.id,
            candidate_report_id=cand["candidate_report_id"],
            distance_meters=cand["distance_meters"],
            category_match=cand["category_match"],
            description_similarity=cand["description_similarity"],
            time_proximity_hours=cand["time_proximity_hours"],
            match_score=cand["match_score"],
            match_explanation=cand["match_explanation"],
            suggested_action=cand["suggested_action"]
        )
        await db.flush()
    
    priority_result = await priority_service.calculate_priority(report, duplicate_count)
    report.priority_score = priority_result.priority_score
    report.priority_band = priority_result.priority_band
    report.priority_version = priority_result.rule_version
    
    priority_assessment = PriorityAssessment(
        report_id=report.id,
        severity_score=priority_result.severity_score,
        risk_score=priority_result.risk_score,
        time_score=priority_result.time_score,
        corroboration_score=priority_result.corroboration_score,
        total_score=priority_result.priority_score,
        priority_band=priority_result.priority_band,
        rule_version=priority_result.rule_version,
        factor_details=priority_result.factor_details,
        escalation_recommended=priority_result.escalation_recommended,
        escalation_reason=priority_result.escalation_reason,
        assessed_by="system"
    )
    await db.flush()
    
    routing = await routing_service.recommend_department(report, priority_result.priority_band)
    report.assigned_department_id = routing.department_id
    report.metadata["routing_recommendation"] = routing.model_dump()
    
    await db.commit()
    await db.refresh(report)
    
    event = ReportEvent(
        report_id=report.id,
        event_type="created",
        new_status=report.status,
        actor_id=current_user.id if current_user else None,
        actor_role=current_user.role if current_user else None,
        reason="Report submitted",
        metadata={"classification": classification.model_dump(), "verification": verification.model_dump()}
    )
    await event_repo.create(event)
    
    await audit_repo.log(
        actor_id=current_user.id if current_user else None,
        actor_role=current_user.role if current_user else None,
        action="create",
        resource_type="report",
        resource_id=report.id,
        new_state={"tracking_id": report.tracking_id, "status": report.status.value}
    )
    
    if current_user:
        notification = Notification(
            user_id=current_user.id,
            report_id=report.id,
            channel=NotificationChannel.IN_APP,
            event_type="report_submitted",
            title="Report Submitted",
            message=f"Your report {report.tracking_id} has been submitted and is under review.",
            data={"report_id": str(report.id), "tracking_id": report.tracking_id}
        )
        await notification_repo.create(notification)
    
    return await _build_report_response(report, db)


@router.get("", response_model=PaginatedResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[List[ReportStatus]] = Query(None),
    category: Optional[List[IssueCategory]] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
    priority_band: Optional[List[PriorityBand]] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius: Optional[int] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report_repo = ReportRepository(db)
    
    filters = {}
    if status:
        filters["status"] = status
    if category:
        filters["category"] = category
    if department_id:
        filters["department_id"] = department_id
    if priority_band:
        filters["priority_band"] = priority_band
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if lat is not None and lng is not None and radius:
        filters["bounds"] = {"lat": lat, "lng": lng, "radius": radius}
    
    items, total = await report_repo.get_list(
        page=page,
        page_size=page_size,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order,
        user_id=current_user.id if current_user.role == UserRole.CITIZEN else None,
        user_role=current_user.role
    )
    
    items_response = []
    for item in items:
        media = await ReportMediaRepository(db).get_by_report(item.id)
        primary = next((m for m in media if m.is_primary), media[0] if media else None)
        items_response.append(ReportListItem(
            id=item.id,
            tracking_id=item.tracking_id,
            title=item.title,
            description=item.description,
            category=item.category,
            coordinates=Coordinates(latitude=item.coordinates.y, longitude=item.coordinates.x),
            address=item.address,
            status=item.status,
            priority_score=item.priority_score,
            priority_band=item.priority_band,
            created_at=item.created_at,
            updated_at=item.updated_at,
            media_count=len(media),
            primary_media=primary
        ))
    
    return PaginatedResponse(
        items=items_response,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await _get_report_with_access(report_id, current_user, db)
    return await _build_report_response(report, db)


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: uuid.UUID,
    report_data: ReportUpdate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report_repo = ReportRepository(db)
    audit_repo = AuditRepository(db)
    
    report = await _get_report_with_access(report_id, current_user, db, allow_edit=True)
    
    previous_state = {
        "title": report.title,
        "description": report.description,
        "category": report.category.value if report.category else None,
        "address": report.address,
        "landmark": report.landmark
    }
    
    update_data = report_data.model_dump(exclude_unset=True)
    if "coordinates" in update_data:
        coords = update_data.pop("coordinates")
        update_data["coordinates"] = f"POINT({coords['longitude']} {coords['latitude']})"
    
    updated = await report_repo.update(report_id, update_data)
    
    await audit_repo.log(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="update",
        resource_type="report",
        resource_id=report_id,
        previous_state=previous_state,
        new_state=update_data
    )
    
    return await _build_report_response(updated, db)


@router.post("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(
    report_id: uuid.UUID,
    status_update: ReportStatusUpdate,
    current_user: Profile = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    report_repo = ReportRepository(db)
    event_repo = ReportEventRepository(db)
    audit_repo = AuditRepository(db)
    notification_repo = NotificationRepository(db)
    
    report = await _get_report_with_access(report_id, current_user, db)
    
    allowed_transitions = {
        ReportStatusEnum.REPORTED: [ReportStatusEnum.UNDER_REVIEW, ReportStatusEnum.REJECTED],
        ReportStatusEnum.UNDER_REVIEW: [ReportStatusEnum.VERIFIED, ReportStatusEnum.NEEDS_MORE_INFO, ReportStatusEnum.REJECTED],
        ReportStatusEnum.NEEDS_MORE_INFO: [ReportStatusEnum.UNDER_REVIEW, ReportStatusEnum.REJECTED],
        ReportStatusEnum.VERIFIED: [ReportStatusEnum.ASSIGNED],
        ReportStatusEnum.ASSIGNED: [ReportStatusEnum.IN_PROGRESS],
        ReportStatusEnum.IN_PROGRESS: [ReportStatusEnum.RESOLVED_PENDING_CONFIRMATION],
        ReportStatusEnum.RESOLVED_PENDING_CONFIRMATION: [ReportStatusEnum.CLOSED, ReportStatusEnum.REOPENED],
        ReportStatusEnum.CLOSED: [ReportStatusEnum.REOPENED],
        ReportStatusEnum.REOPENED: [ReportStatusEnum.UNDER_REVIEW],
    }
    
    new_status = ReportStatusEnum(status_update.status.value)
    if new_status not in allowed_transitions.get(report.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {report.status.value} to {new_status.value}"
        )
    
    previous_status = report.status
    report.status = new_status
    report.updated_at = datetime.utcnow()
    
    if new_status == ReportStatusEnum.VERIFIED:
        report.verified_at = datetime.utcnow()
    elif new_status == ReportStatusEnum.ASSIGNED:
        report.assigned_at = datetime.utcnow()
    elif new_status == ReportStatusEnum.RESOLVED_PENDING_CONFIRMATION:
        report.resolved_at = datetime.utcnow()
    elif new_status == ReportStatusEnum.CLOSED:
        report.closed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(report)
    
    event = ReportEvent(
        report_id=report.id,
        event_type="status_change",
        previous_status=previous_status,
        new_status=new_status,
        actor_id=current_user.id,
        actor_role=current_user.role,
        reason=status_update.reason
    )
    await event_repo.create(event)
    
    await audit_repo.log(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="status_change",
        resource_type="report",
        resource_id=report_id,
        previous_state={"status": previous_status.value},
        new_state={"status": new_status.value, "reason": status_update.reason}
    )
    
    if report.reporter_id and report.reporter_id != current_user.id:
        notification = Notification(
            user_id=report.reporter_id,
            report_id=report.id,
            channel=NotificationChannel.IN_APP,
            event_type="status_update",
            title="Report Status Updated",
            message=f"Your report {report.tracking_id} status changed to {new_status.value.replace('_', ' ').title()}.",
            data={"report_id": str(report.id), "new_status": new_status.value}
        )
        await notification_repo.create(notification)
    
    return await _build_report_response(report, db)


@router.post("/{report_id}/assign", response_model=AssignmentResponse)
async def assign_report(
    report_id: uuid.UUID,
    assign_data: ReportAssign,
    current_user: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    report_repo = ReportRepository(db)
    assignment_repo = AssignmentRepository(db)
    event_repo = ReportEventRepository(db)
    audit_repo = AuditRepository(db)
    notification_repo = NotificationRepository(db)
    dept_repo = DepartmentRepository(db)
    
    report = await _get_report_with_access(report_id, current_user, db)
    
    if report.status not in [ReportStatusEnum.VERIFIED, ReportStatusEnum.ASSIGNED]:
        raise HTTPException(status_code=400, detail="Report must be verified before assignment")
    
    dept = await dept_repo.get_by_id(assign_data.department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    report.assigned_department_id = assign_data.department_id
    report.status = ReportStatusEnum.ASSIGNED
    report.assigned_at = datetime.utcnow()
    
    assignment = Assignment(
        report_id=report.id,
        department_id=assign_data.department_id,
        worker_id=assign_data.worker_id,
        assigned_by=current_user.id,
        status=AssignmentStatus.PENDING,
        instructions=assign_data.instructions,
        sla_deadline=assign_data.sla_deadline or datetime.utcnow() + timedelta(hours=dept.sla_hours)
    )
    await assignment_repo.create(assignment)
    
    await db.commit()
    
    event = ReportEvent(
        report_id=report.id,
        event_type="assigned",
        previous_status=ReportStatusEnum.VERIFIED,
        new_status=ReportStatusEnum.ASSIGNED,
        actor_id=current_user.id,
        actor_role=current_user.role,
        reason=f"Assigned to {dept.name}",
        metadata={"department_id": str(assign_data.department_id), "worker_id": str(assign_data.worker_id) if assign_data.worker_id else None}
    )
    await event_repo.create(event)
    
    await audit_repo.log(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="assign",
        resource_type="report",
        resource_id=report_id,
        new_state={"department_id": str(assign_data.department_id), "worker_id": str(assign_data.worker_id) if assign_data.worker_id else None}
    )
    
    if assign_data.worker_id:
        notification = Notification(
            user_id=assign_data.worker_id,
            report_id=report.id,
            channel=NotificationChannel.IN_APP,
            event_type="assigned",
            title="New Assignment",
            message=f"You have been assigned to report {report.tracking_id}.",
            data={"report_id": str(report.id), "assignment_id": str(assignment.id)}
        )
        await notification_repo.create(notification)
    
    return await _build_assignment_response(assignment, db)


@router.get("/{report_id}/timeline", response_model=List[dict])
async def get_report_timeline(
    report_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await _get_report_with_access(report_id, current_user, db)
    event_repo = ReportEventRepository(db)
    comment_repo = ReportCommentRepository(db)
    
    events = await event_repo.get_by_report(report_id)
    comments = await comment_repo.get_by_report(report_id)
    
    timeline = []
    for event in events:
        timeline.append({
            "id": str(event.id),
            "type": "event",
            "event_type": event.event_type,
            "previous_status": event.previous_status.value if event.previous_status else None,
            "new_status": event.new_status.value if event.new_status else None,
            "actor_id": str(event.actor_id) if event.actor_id else None,
            "actor_role": event.actor_role.value if event.actor_role else None,
            "reason": event.reason,
            "metadata": event.metadata,
            "created_at": event.created_at.isoformat()
        })
    
    for comment in comments:
        timeline.append({
            "id": str(comment.id),
            "type": "comment",
            "content": comment.content,
            "is_internal": comment.is_internal,
            "author_id": str(comment.author_id),
            "author_name": comment.author.full_name if comment.author else None,
            "author_role": comment.author.role.value if comment.author else None,
            "created_at": comment.created_at.isoformat()
        })
    
    timeline.sort(key=lambda x: x["created_at"])
    return timeline


@router.post("/{report_id}/comments", response_model=ReportCommentResponse)
async def add_comment(
    report_id: uuid.UUID,
    comment_data: ReportCommentCreate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.repositories import ReportCommentRepository
    
    report = await _get_report_with_access(report_id, current_user, db)
    comment_repo = ReportCommentRepository(db)
    
    is_staff = current_user.role in [UserRole.ADMIN, UserRole.FIELD_WORKER, UserRole.SUPERVISOR]
    
    comment = ReportComment(
        report_id=report.id,
        author_id=current_user.id,
        content=comment_data.content,
        is_internal=comment_data.is_internal and is_staff
    )
    await comment_repo.create(comment)
    await db.refresh(comment, attribute_names=["author"])
    
    return comment


@router.get("/{report_id}/duplicates", response_model=List[DuplicateCandidateResponse])
async def get_duplicate_candidates(
    report_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await _get_report_with_access(report_id, current_user, db)
    dup_repo = DuplicateRepository(db)
    
    candidates = await dup_repo.get_candidates_for_report(report_id)
    
    result = []
    for cand in candidates:
        cand_report = await ReportRepository(db).get_by_id(cand.candidate_report_id)
        if cand_report:
            result.append(DuplicateCandidateResponse(
                id=cand.id,
                report_id=cand.report_id,
                candidate_report_id=cand.candidate_report_id,
                candidate_tracking_id=cand_report.tracking_id,
                candidate_title=cand_report.title,
                candidate_category=cand_report.category,
                candidate_coordinates=Coordinates(latitude=cand_report.coordinates.y, longitude=cand_report.coordinates.x),
                candidate_status=cand_report.status,
                distance_meters=cand.distance_meters,
                category_match=cand.category_match,
                description_similarity=cand.description_similarity,
                image_similarity=cand.image_similarity,
                time_proximity_hours=cand.time_proximity_hours,
                match_score=cand.match_score,
                match_explanation=cand.match_explanation,
                suggested_action=cand.suggested_action,
                status=cand.status,
                reviewed_by=cand.reviewed_by,
                reviewed_at=cand.reviewed_at,
                review_reason=cand.review_reason,
                created_at=cand.created_at
            ))
    
    return result


@router.post("/{report_id}/duplicates/{candidate_id}/review", response_model=DuplicateCandidateResponse)
async def review_duplicate(
    report_id: uuid.UUID,
    candidate_id: uuid.UUID,
    review: DuplicateReviewRequest,
    current_user: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    dup_repo = DuplicateRepository(db)
    audit_repo = AuditRepository(db)
    
    candidate = await dup_repo.get_by_id(candidate_id)
    if not candidate or candidate.report_id != report_id:
        raise HTTPException(status_code=404, detail="Duplicate candidate not found")
    
    updated = await dup_repo.update_status(candidate_id, review.action, current_user.id, review.reason)
    
    if review.action == "confirm":
        from app.models import ReportLink
        link = ReportLink(
            primary_report_id=report_id,
            duplicate_report_id=candidate.candidate_report_id,
            linked_by=current_user.id,
            link_reason=review.reason
        )
        await dup_repo.create_link(link)
        
        candidate_report = await ReportRepository(db).get_by_id(candidate.candidate_report_id)
        candidate_report.duplicate_primary_id = report_id
        candidate_report.status = ReportStatusEnum.CLOSED
    
    await audit_repo.log(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action=f"duplicate_{review.action}",
        resource_type="duplicate_candidate",
        resource_id=candidate_id,
        new_state={"action": review.action, "reason": review.reason}
    )
    
    return updated


@router.post("/{report_id}/resolution", response_model=ResolutionEvidenceResponse)
async def submit_resolution(
    report_id: uuid.UUID,
    resolution_data: ResolutionEvidenceCreate,
    current_user: Profile = Depends(require_field_worker),
    db: AsyncSession = Depends(get_db)
):
    report_repo = ReportRepository(db)
    resolution_repo = ResolutionRepository(db)
    event_repo = ReportEventRepository(db)
    audit_repo = AuditRepository(db)
    notification_repo = NotificationRepository(db)
    
    report = await _get_report_with_access(report_id, current_user, db)
    
    if report.status != ReportStatusEnum.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Report must be in progress to submit resolution")
    
    if report.assignee_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        raise HTTPException(status_code=403, detail="Not assigned to this report")
    
    resolution = ResolutionEvidence(
        report_id=report.id,
        assignment_id=resolution_data.assignment_id,
        submitted_by_id=current_user.id,
        before_media=resolution_data.before_media,
        after_media=resolution_data.after_media,
        work_notes=resolution_data.work_notes
    )
    await resolution_repo.create(resolution)
    
    report.status = ReportStatusEnum.RESOLVED_PENDING_CONFIRMATION
    report.resolved_at = datetime.utcnow()
    
    event = ReportEvent(
        report_id=report.id,
        event_type="resolution_submitted",
        previous_status=ReportStatusEnum.IN_PROGRESS,
        new_status=ReportStatusEnum.RESOLVED_PENDING_CONFIRMATION,
        actor_id=current_user.id,
        actor_role=current_user.role,
        reason="Resolution evidence submitted",
        metadata={"resolution_id": str(resolution.id)}
    )
    await event_repo.create(event)
    
    await audit_repo.log(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="submit_resolution",
        resource_type="report",
        resource_id=report_id,
        new_state={"resolution_id": str(resolution.id)}
    )
    
    if report.reporter_id:
        notification = Notification(
            user_id=report.reporter_id,
            report_id=report.id,
            channel=NotificationChannel.IN_APP,
            event_type="resolved",
            title="Report Resolved",
            message=f"Report {report.tracking_id} has been marked as resolved. Please review.",
            data={"report_id": str(report.id), "resolution_id": str(resolution.id)}
        )
        await notification_repo.create(notification)
    
    await db.commit()
    await db.refresh(resolution)
    return resolution


@router.post("/{report_id}/resolution/review", response_model=ResolutionEvidenceResponse)
async def review_resolution(
    report_id: uuid.UUID,
    review: ResolutionReviewRequest,
    current_user: Profile = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db)
):
    resolution_repo = ResolutionRepository(db)
    report_repo = ReportRepository(db)
    event_repo = ReportEventRepository(db)
    audit_repo = AuditRepository(db)
    notification_repo = NotificationRepository(db)
    
    resolutions = await resolution_repo.get_by_report(report_id)
    resolution = next((r for r in resolutions if r.status == ResolutionStatus.SUBMITTED), None)
    
    if not resolution:
        raise HTTPException(status_code=404, detail="No pending resolution to review")
    
    report = await report_repo.get_by_id(report_id)
    
    if review.action == "approve":
        resolution.status = ResolutionStatus.APPROVED
        report.status = ReportStatusEnum.CLOSED
        report.closed_at = datetime.utcnow()
        event_type = "resolution_approved"
        message = f"Resolution for report {report.tracking_id} has been approved."
    elif review.action == "reject":
        resolution.status = ResolutionStatus.REJECTED
        report.status = ReportStatusEnum.IN_PROGRESS
        event_type = "resolution_rejected"
        message = f"Resolution for report {report.tracking_id} was rejected. Work continues."
    else:
        resolution.status = ResolutionStatus.NEEDS_REWORK
        report.status = ReportStatusEnum.IN_PROGRESS
        event_type = "resolution_needs_rework"
        message = f"Resolution for report {report.tracking_id} needs rework."
    
    resolution.reviewed_by = current_user.id
    resolution.reviewed_at = datetime.utcnow()
    resolution.review_notes = review.notes
    
    await db.commit()
    
    event = ReportEvent(
        report_id=report.id,
        event_type=event_type,
        previous_status=ReportStatusEnum.RESOLVED_PENDING_CONFIRMATION,
        new_status=report.status,
        actor_id=current_user.id,
        actor_role=current_user.role,
        reason=review.notes,
        metadata={"resolution_id": str(resolution.id)}
    )
    await event_repo.create(event)
    
    await audit_repo.log(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action=f"resolution_{review.action}",
        resource_type="resolution",
        resource_id=resolution.id,
        new_state={"action": review.action, "notes": review.notes}
    )
    
    if report.reporter_id:
        notification = Notification(
            user_id=report.reporter_id,
            report_id=report.id,
            channel=NotificationChannel.IN_APP,
            event_type=event_type,
            title="Resolution Update",
            message=message,
            data={"report_id": str(report.id), "resolution_id": str(resolution.id)}
        )
        await notification_repo.create(notification)
    
    await db.refresh(resolution)
    return resolution


async def _get_report_with_access(
    report_id: uuid.UUID,
    current_user: Profile,
    db: AsyncSession,
    allow_edit: bool = False
) -> Report:
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(report_id, load_relations=True)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if current_user.role == UserRole.CITIZEN:
        if report.reporter_id != current_user.id:
            if not report.is_public:
                raise HTTPException(status_code=403, detail="Access denied")
        if allow_edit and report.reporter_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot edit other users' reports")
    elif current_user.role == UserRole.FIELD_WORKER:
        if report.assignee_id != current_user.id and not allow_edit:
            raise HTTPException(status_code=403, detail="Not assigned to this report")
    
    return report


async def _build_report_response(report: Report, db: AsyncSession) -> ReportResponse:
    media_repo = ReportMediaRepository(db)
    media = await media_repo.get_by_report(report.id)
    
    return ReportResponse(
        id=report.id,
        tracking_id=report.tracking_id,
        title=report.title,
        description=report.description,
        category=report.category,
        category_confidence=report.category_confidence,
        category_source=report.category_source,
        coordinates=Coordinates(latitude=report.coordinates.y, longitude=report.coordinates.x),
        address=report.address,
        landmark=report.landmark,
        status=report.status,
        priority_score=report.priority_score,
        priority_band=report.priority_band,
        priority_version=report.priority_version,
        assigned_department_id=report.assigned_department_id,
        reporter_id=report.reporter_id,
        assignee_id=report.assignee_id,
        is_anonymous=report.is_anonymous,
        is_public=report.is_public,
        duplicate_primary_id=report.duplicate_primary_id,
        metadata=report.metadata,
        created_at=report.created_at,
        updated_at=report.updated_at,
        verified_at=report.verified_at,
        assigned_at=report.assigned_at,
        resolved_at=report.resolved_at,
        closed_at=report.closed_at,
        media=media
    )


async def _build_assignment_response(assignment: Assignment, db: AsyncSession) -> AssignmentResponse:
    dept_repo = DepartmentRepository(db)
    dept = await dept_repo.get_by_id(assignment.department_id)
    worker = None
    if assignment.worker_id:
        from app.repositories import ProfileRepository
        worker = await ProfileRepository(db).get_by_id(assignment.worker_id)
    
    return AssignmentResponse(
        id=assignment.id,
        report_id=assignment.report_id,
        department_id=assignment.department_id,
        worker_id=assignment.worker_id,
        assigned_by=assignment.assigned_by,
        status=assignment.status,
        priority=assignment.priority,
        instructions=assignment.instructions,
        sla_deadline=assignment.sla_deadline,
        accepted_at=assignment.accepted_at,
        started_at=assignment.started_at,
        completed_at=assignment.completed_at,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        department=dept,
        worker=worker
    )


@router.get("/{report_id}/analysis", response_model=dict)
async def get_report_analysis(
    report_id: uuid.UUID,
    current_user: Profile = Depends(require_staff),
    db: AsyncSession = Depends(get_db)
):
    from app.repositories import AgentRunRepository
    
    report = await _get_report_with_access(report_id, current_user, db)
    agent_repo = AgentRunRepository(db)
    
    runs = await agent_repo.get_by_report(report_id)
    
    return {
        "report_id": str(report_id),
        "classification": {
            "category": report.category.value,
            "confidence": report.category_confidence,
            "source": report.category_source,
            "ai_suggested": report.metadata.get("ai_suggested_category")
        },
        "priority": {
            "score": report.priority_score,
            "band": report.priority_band.value,
            "version": report.priority_version
        },
        "duplicates": [str(c.candidate_report_id) for c in await DuplicateRepository(db).get_candidates_for_report(report_id)],
        "routing": report.metadata.get("routing_recommendation"),
        "agent_runs": [
            {
                "agent_type": r.agent_type,
                "status": r.status,
                "output": r.output_data,
                "created_at": r.created_at.isoformat()
            }
            for r in runs
        ]
    }