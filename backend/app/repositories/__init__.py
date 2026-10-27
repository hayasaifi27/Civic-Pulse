from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, delete, update
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeogFromText, ST_MakePoint
from geoalchemy2.shape import to_shape

from app.models import (
    Profile, Department, ServiceZone, ConfigurableCategory, RoutingRule,
    Report, ReportMedia, ReportEvent, ReportComment, DuplicateCandidate,
    ReportLink, Assignment, ResolutionEvidence, PriorityAssessment,
    AgentRun, Notification, Feedback, AuditLog, ModerationAction, ScoringRule,
    UserRole, ReportStatus, IssueCategory, PriorityBand, DuplicateStatus,
    AssignmentStatus, ResolutionStatus
)
from app.schemas import Coordinates


class ProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[Profile]:
        result = await self.db.execute(select(Profile).where(Profile.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Profile]:
        result = await self.db.execute(select(Profile).where(Profile.email == email))
        return result.scalar_one_or_none()

    async def create(self, profile: Profile) -> Profile:
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update(self, user_id: UUID, data: Dict[str, Any]) -> Optional[Profile]:
        profile = await self.get_by_id(user_id)
        if profile:
            for key, value in data.items():
                setattr(profile, key, value)
            await self.db.flush()
            await self.db.refresh(profile)
        return profile

    async def get_by_role(self, role: UserRole, limit: int = 100, offset: int = 0) -> List[Profile]:
        result = await self.db.execute(
            select(Profile).where(Profile.role == role).limit(limit).offset(offset)
        )
        return list(result.scalars().all())


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, active_only: bool = True) -> List[ConfigurableCategory]:
        query = select(ConfigurableCategory).order_by(ConfigurableCategory.sort_order)
        if active_only:
            query = query.where(ConfigurableCategory.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: UUID) -> Optional[ConfigurableCategory]:
        result = await self.db.execute(select(ConfigurableCategory).where(ConfigurableCategory.id == category_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[ConfigurableCategory]:
        result = await self.db.execute(select(ConfigurableCategory).where(ConfigurableCategory.code == code))
        return result.scalar_one_or_none()

    async def create(self, category: ConfigurableCategory) -> ConfigurableCategory:
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: UUID, data: Dict[str, Any]) -> Optional[ConfigurableCategory]:
        category = await self.get_by_id(category_id)
        if category:
            for key, value in data.items():
                setattr(category, key, value)
            await self.db.flush()
            await self.db.refresh(category)
        return category


class DepartmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, active_only: bool = True) -> List[Department]:
        query = select(Department).order_by(Department.name)
        if active_only:
            query = query.where(Department.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, dept_id: UUID) -> Optional[Department]:
        result = await self.db.execute(select(Department).where(Department.id == dept_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Department]:
        result = await self.db.execute(select(Department).where(Department.code == code))
        return result.scalar_one_or_none()

    async def create(self, department: Department) -> Department:
        self.db.add(department)
        await self.db.flush()
        await self.db.refresh(department)
        return department


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, report: Report) -> Report:
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def get_by_id(self, report_id: UUID, load_relations: bool = False) -> Optional[Report]:
        query = select(Report).where(Report.id == report_id)
        if load_relations:
            query = query.options(
                selectinload(Report.media),
                selectinload(Report.assigned_department),
                selectinload(Report.reporter),
                selectinload(Report.assignee)
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_tracking_id(self, tracking_id: str) -> Optional[Report]:
        result = await self.db.execute(select(Report).where(Report.tracking_id == tracking_id))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        user_id: Optional[UUID] = None,
        user_role: Optional[UserRole] = None
    ) -> Tuple[List[Report], int]:
        query = select(Report)
        count_query = select(func.count(Report.id))

        if user_role == UserRole.CITIZEN and user_id:
            query = query.where(Report.reporter_id == user_id)
            count_query = count_query.where(Report.reporter_id == user_id)
        elif user_role == UserRole.FIELD_WORKER and user_id:
            query = query.where(Report.assignee_id == user_id)
            count_query = count_query.where(Report.assignee_id == user_id)

        if filters:
            if filters.get("status"):
                query = query.where(Report.status.in_(filters["status"]))
                count_query = count_query.where(Report.status.in_(filters["status"]))
            if filters.get("category"):
                query = query.where(Report.category.in_(filters["category"]))
                count_query = count_query.where(Report.category.in_(filters["category"]))
            if filters.get("department_id"):
                query = query.where(Report.assigned_department_id == filters["department_id"])
                count_query = count_query.where(Report.assigned_department_id == filters["department_id"])
            if filters.get("priority_band"):
                query = query.where(Report.priority_band.in_(filters["priority_band"]))
                count_query = count_query.where(Report.priority_band.in_(filters["priority_band"]))
            if filters.get("date_from"):
                query = query.where(Report.created_at >= filters["date_from"])
                count_query = count_query.where(Report.created_at >= filters["date_from"])
            if filters.get("date_to"):
                query = query.where(Report.created_at <= filters["date_to"])
                count_query = count_query.where(Report.created_at <= filters["date_to"])
            if filters.get("bounds"):
                bounds = filters["bounds"]
                query = query.where(
                    ST_DWithin(
                        Report.coordinates,
                        ST_MakePoint(bounds["lng"], bounds["lat"]),
                        bounds["radius"]
                    )
                )
                count_query = count_query.where(
                    ST_DWithin(
                        Report.coordinates,
                        ST_MakePoint(bounds["lng"], bounds["lat"]),
                        bounds["radius"]
                    )
                )

        sort_column = getattr(Report, sort_by, Report.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.limit(page_size).offset((page - 1) * page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(self, report_id: UUID, data: Dict[str, Any]) -> Optional[Report]:
        report = await self.get_by_id(report_id)
        if report:
            for key, value in data.items():
                setattr(report, key, value)
            report.updated_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(report)
        return report

    async def find_nearby(
        self,
        coordinates: Coordinates,
        category: Optional[IssueCategory] = None,
        radius_meters: int = 100,
        exclude_id: Optional[UUID] = None,
        status_filter: Optional[List[ReportStatus]] = None,
        limit: int = 10
    ) -> List[Report]:
        point = ST_MakePoint(coordinates.longitude, coordinates.latitude)
        query = select(Report).where(
            ST_DWithin(Report.coordinates, point, radius_meters)
        )
        if category:
            query = query.where(Report.category == category)
        if exclude_id:
            query = query.where(Report.id != exclude_id)
        if status_filter:
            query = query.where(Report.status.in_(status_filter))
        else:
            query = query.where(Report.status.not_in([ReportStatus.REJECTED, ReportStatus.CLOSED]))
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class ReportMediaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, media: ReportMedia) -> ReportMedia:
        self.db.add(media)
        await self.db.flush()
        await self.db.refresh(media)
        return media

    async def get_by_report(self, report_id: UUID) -> List[ReportMedia]:
        result = await self.db.execute(
            select(ReportMedia).where(ReportMedia.report_id == report_id).order_by(ReportMedia.sort_order)
        )
        return list(result.scalars().all())

    async def set_primary(self, report_id: UUID, media_id: UUID) -> bool:
        await self.db.execute(
            update(ReportMedia).where(ReportMedia.report_id == report_id).values(is_primary=False)
        )
        result = await self.db.execute(
            update(ReportMedia)
            .where(ReportMedia.id == media_id, ReportMedia.report_id == report_id)
            .values(is_primary=True)
        )
        return result.rowcount > 0


class ReportEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event: ReportEvent) -> ReportEvent:
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def get_by_report(self, report_id: UUID) -> List[ReportEvent]:
        result = await self.db.execute(
            select(ReportEvent).where(ReportEvent.report_id == report_id).order_by(ReportEvent.created_at)
        )
        return list(result.scalars().all())


class DuplicateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_candidate(self, candidate: DuplicateCandidate) -> DuplicateCandidate:
        self.db.add(candidate)
        await self.db.flush()
        await self.db.refresh(candidate)
        return candidate

    async def get_candidates_for_report(self, report_id: UUID) -> List[DuplicateCandidate]:
        result = await self.db.execute(
            select(DuplicateCandidate)
            .where(DuplicateCandidate.report_id == report_id)
            .order_by(DuplicateCandidate.match_score.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, candidate_id: UUID) -> Optional[DuplicateCandidate]:
        result = await self.db.execute(select(DuplicateCandidate).where(DuplicateCandidate.id == candidate_id))
        return result.scalar_one_or_none()

    async def update_status(
        self,
        candidate_id: UUID,
        status: DuplicateStatus,
        reviewed_by: UUID,
        reason: Optional[str] = None
    ) -> Optional[DuplicateCandidate]:
        candidate = await self.get_by_id(candidate_id)
        if candidate:
            candidate.status = status
            candidate.reviewed_by = reviewed_by
            candidate.reviewed_at = datetime.utcnow()
            candidate.review_reason = reason
            await self.db.flush()
            await self.db.refresh(candidate)
        return candidate

    async def create_link(self, link: ReportLink) -> ReportLink:
        self.db.add(link)
        await self.db.flush()
        await self.db.refresh(link)
        return link

    async def get_links_for_primary(self, primary_id: UUID) -> List[ReportLink]:
        result = await self.db.execute(select(ReportLink).where(ReportLink.primary_report_id == primary_id))
        return list(result.scalars().all())

    async def unlink(self, primary_id: UUID, duplicate_id: UUID, unlinked_by: UUID, reason: str) -> bool:
        link_result = await self.db.execute(
            delete(ReportLink).where(
                ReportLink.primary_report_id == primary_id,
                ReportLink.duplicate_report_id == duplicate_id
            )
        )
        if link_result.rowcount > 0:
            await self.db.execute(
                update(DuplicateCandidate)
                .where(
                    DuplicateCandidate.report_id == primary_id,
                    DuplicateCandidate.candidate_report_id == duplicate_id
                )
                .values(status=DuplicateStatus.UNLINKED, reviewed_by=unlinked_by, review_reason=reason)
            )
            return True
        return False


class AssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, assignment: Assignment) -> Assignment:
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def get_by_id(self, assignment_id: UUID) -> Optional[Assignment]:
        result = await self.db.execute(
            select(Assignment).options(
                selectinload(Assignment.department),
                selectinload(Assignment.worker)
            ).where(Assignment.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_report(self, report_id: UUID) -> List[Assignment]:
        result = await self.db.execute(
            select(Assignment).where(Assignment.report_id == report_id).order_by(Assignment.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_worker_assignments(
        self,
        worker_id: UUID,
        status_filter: Optional[List[AssignmentStatus]] = None
    ) -> List[Assignment]:
        query = select(Assignment).where(Assignment.worker_id == worker_id)
        if status_filter:
            query = query.where(Assignment.status.in_(status_filter))
        query = query.order_by(Assignment.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, assignment_id: UUID, data: Dict[str, Any]) -> Optional[Assignment]:
        assignment = await self.get_by_id(assignment_id)
        if assignment:
            for key, value in data.items():
                setattr(assignment, key, value)
            assignment.updated_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(assignment)
        return assignment


class ResolutionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, resolution: ResolutionEvidence) -> ResolutionEvidence:
        self.db.add(resolution)
        await self.db.flush()
        await self.db.refresh(resolution)
        return resolution

    async def get_by_report(self, report_id: UUID) -> List[ResolutionEvidence]:
        result = await self.db.execute(
            select(ResolutionEvidence).where(ResolutionEvidence.report_id == report_id).order_by(ResolutionEvidence.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_pending_review(self, reviewer_role: UserRole = UserRole.SUPERVISOR) -> List[ResolutionEvidence]:
        result = await self.db.execute(
            select(ResolutionEvidence)
            .where(ResolutionEvidence.status == ResolutionStatus.SUBMITTED)
            .order_by(ResolutionEvidence.created_at)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        resolution_id: UUID,
        status: ResolutionStatus,
        reviewed_by: UUID,
        notes: Optional[str] = None
    ) -> Optional[ResolutionEvidence]:
        result = await self.db.execute(select(ResolutionEvidence).where(ResolutionEvidence.id == resolution_id))
        resolution = result.scalar_one_or_none()
        if resolution:
            resolution.status = status
            resolution.reviewed_by = reviewed_by
            resolution.reviewed_at = datetime.utcnow()
            resolution.review_notes = notes
            await self.db.flush()
            await self.db.refresh(resolution)
        return resolution


class PriorityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, assessment: PriorityAssessment) -> PriorityAssessment:
        self.db.add(assessment)
        await self.db.flush()
        await self.db.refresh(assessment)
        return assessment

    async def get_latest_for_report(self, report_id: UUID) -> Optional[PriorityAssessment]:
        result = await self.db.execute(
            select(PriorityAssessment)
            .where(PriorityAssessment.report_id == report_id)
            .order_by(PriorityAssessment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_active_rule(self) -> Optional[ScoringRule]:
        result = await self.db.execute(
            select(ScoringRule).where(ScoringRule.is_active == True).order_by(ScoringRule.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()


class AgentRunRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, run: AgentRun) -> AgentRun:
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def get_by_report(self, report_id: UUID, agent_type: Optional[str] = None) -> List[AgentRun]:
        query = select(AgentRun).where(AgentRun.report_id == report_id)
        if agent_type:
            query = query.where(AgentRun.agent_type == agent_type)
        query = query.order_by(AgentRun.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        query = query.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> bool:
        result = await self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True, read_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def mark_all_read(self, user_id: UUID) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=datetime.utcnow())
        )
        return result.rowcount


class ServiceZoneRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, active_only: bool = True) -> List[ServiceZone]:
        query = select(ServiceZone).order_by(ServiceZone.name)
        if active_only:
            query = query.where(ServiceZone.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, zone_id: UUID) -> Optional[ServiceZone]:
        result = await self.db.execute(select(ServiceZone).where(ServiceZone.id == zone_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[ServiceZone]:
        result = await self.db.execute(select(ServiceZone).where(ServiceZone.code == code))
        return result.scalar_one_or_none()

    async def create(self, zone: ServiceZone) -> ServiceZone:
        self.db.add(zone)
        await self.db.flush()
        await self.db.refresh(zone)
        return zone


class RoutingRuleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, category_id: Optional[UUID] = None) -> List[RoutingRule]:
        query = select(RoutingRule).where(RoutingRule.is_active == True)
        if category_id:
            query = query.where(RoutingRule.category_id == category_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, rule: RoutingRule) -> RoutingRule:
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule


class ScoringRuleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[ScoringRule]:
        result = await self.db.execute(select(ScoringRule).order_by(ScoringRule.created_at.desc()))
        return list(result.scalars().all())


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        actor_id: Optional[UUID],
        actor_role: Optional[UserRole],
        action: str,
        resource_type: str,
        resource_id: Optional[UUID],
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            previous_state=previous_state,
            new_state=new_state,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
        await self.db.flush()
        return log