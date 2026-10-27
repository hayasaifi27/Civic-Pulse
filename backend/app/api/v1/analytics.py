from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import get_db
from app.core.security import require_admin
from app.models import (
    Report, Department, Assignment, ResolutionEvidence,
    ReportStatus, AssignmentStatus, IssueCategory, PriorityBand, UserRole
)
from app.schemas import (
    AnalyticsOverview, CategoryDistribution, DepartmentWorkload,
    HotspotData, TimeSeriesData, TimeSeriesPoint, Coordinates
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=30)
    if not date_to:
        date_to = datetime.utcnow()
    
    base_query = select(Report).where(
        Report.created_at >= date_from,
        Report.created_at <= date_to
    )
    
    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar()
    
    awaiting_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Report.status.in_([ReportStatus.REPORTED, ReportStatus.UNDER_REVIEW, ReportStatus.NEEDS_MORE_INFO])).subquery()
        )
    )
    awaiting = awaiting_result.scalar()
    
    assigned_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Report.status.in_([ReportStatus.ASSIGNED, ReportStatus.IN_PROGRESS])).subquery()
        )
    )
    assigned = assigned_result.scalar()
    
    overdue_result = await db.execute(
        select(func.count()).select_from(
            select(Assignment).where(
                Assignment.sla_deadline < datetime.utcnow(),
                Assignment.status.in_([AssignmentStatus.PENDING, AssignmentStatus.ACCEPTED, AssignmentStatus.IN_PROGRESS])
            ).subquery()
        )
    )
    overdue = overdue_result.scalar()
    
    resolved_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Report.status.in_([ReportStatus.RESOLVED_PENDING_CONFIRMATION, ReportStatus.CLOSED])).subquery()
        )
    )
    resolved = resolved_result.scalar()
    
    ack_times = await db.execute(
        select(
            func.avg(func.extract('epoch', Report.verified_at - Report.created_at) / 3600)
        ).where(
            Report.verified_at.isnot(None),
            Report.created_at >= date_from,
            Report.created_at <= date_to
        )
    )
    median_ack = ack_times.scalar()
    
    res_times = await db.execute(
        select(
            func.avg(func.extract('epoch', Report.resolved_at - Report.created_at) / 3600)
        ).where(
            Report.resolved_at.isnot(None),
            Report.created_at >= date_from,
            Report.created_at <= date_to
        )
    )
    median_res = res_times.scalar()
    
    resolution_rate = (resolved / total * 100) if total > 0 else 0
    
    reopened_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Report.status == ReportStatus.REOPENED).subquery()
        )
    )
    reopened = reopened_result.scalar()
    reopened_rate = (reopened / resolved * 100) if resolved > 0 else 0
    
    return AnalyticsOverview(
        total_reports=total,
        reports_awaiting_review=awaiting,
        active_assignments=assigned,
        overdue_issues=overdue,
        resolved_closed=resolved,
        median_time_to_acknowledgment_hours=round(median_ack, 1) if median_ack else None,
        median_time_to_resolution_hours=round(median_res, 1) if median_res else None,
        resolution_rate=round(resolution_rate, 1),
        reopened_rate=round(reopened_rate, 1)
    )


@router.get("/categories", response_model=List[CategoryDistribution])
async def get_category_distribution(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=30)
    if not date_to:
        date_to = datetime.utcnow()
    
    result = await db.execute(
        select(Report.category, func.count(Report.id))
        .where(Report.created_at >= date_from, Report.created_at <= date_to)
        .group_by(Report.category)
        .order_by(func.count(Report.id).desc())
    )
    
    total = sum(row[1] for row in result.all())
    
    return [
        CategoryDistribution(
            category=row[0],
            count=row[1],
            percentage=round(row[1] / total * 100, 1) if total > 0 else 0
        )
        for row in result.all()
    ]


@router.get("/departments", response_model=List[DepartmentWorkload])
async def get_department_workload(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(
            Department.id,
            Department.name,
            func.count(Assignment.id).filter(Assignment.status == AssignmentStatus.PENDING).label("assigned"),
            func.count(Assignment.id).filter(Assignment.status == AssignmentStatus.IN_PROGRESS).label("in_progress"),
            func.count(Assignment.id).filter(Assignment.status == AssignmentStatus.COMPLETED).label("completed"),
            func.count(Assignment.id).filter(
                Assignment.sla_deadline < datetime.utcnow(),
                Assignment.status.in_([AssignmentStatus.PENDING, AssignmentStatus.ACCEPTED, AssignmentStatus.IN_PROGRESS])
            ).label("overdue"),
            func.avg(func.extract('epoch', Assignment.completed_at - Assignment.created_at) / 3600).label("avg_resolution")
        )
        .join(Assignment, Department.id == Assignment.department_id, isouter=True)
        .group_by(Department.id, Department.name)
    )
    
    return [
        DepartmentWorkload(
            department_id=row[0],
            department_name=row[1],
            assigned=row[2] or 0,
            in_progress=row[3] or 0,
            completed=row[4] or 0,
            overdue=row[5] or 0,
            avg_resolution_hours=round(row[6], 1) if row[6] else None
        )
        for row in result.all()
    ]


@router.get("/hotspots", response_model=List[HotspotData])
async def get_hotspots(
    radius: int = Query(500, ge=100, le=5000),
    min_count: int = Query(3, ge=2),
    date_from: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=90)
    
    from geoalchemy2.functions import ST_ClusterDBSCAN, ST_Centroid, ST_AsGeoJSON
    from sqlalchemy import text
    
    query = text("""
        WITH clustered AS (
            SELECT 
                id,
                category,
                priority_score,
                ST_AsGeoJSON(coordinates) as geom,
                ST_ClusterDBSCAN(coordinates, :radius, :min_count) OVER () as cluster_id
            FROM reports
            WHERE created_at >= :date_from
              AND status NOT IN ('rejected', 'closed')
        ),
        clusters AS (
            SELECT 
                cluster_id,
                COUNT(*) as count,
                AVG(priority_score) as avg_priority,
                jsonb_agg(DISTINCT category) as categories,
                ST_AsGeoJSON(ST_Centroid(ST_Collect(ST_GeomFromGeoJSON(geom)))) as centroid
            FROM clustered
            WHERE cluster_id IS NOT NULL
            GROUP BY cluster_id
            HAVING COUNT(*) >= :min_count
        )
        SELECT 
            centroid,
            count,
            categories,
            avg_priority
        FROM clusters
        ORDER BY count DESC
        LIMIT 50
    """)
    
    result = await db.execute(query, {"radius": radius, "min_count": min_count, "date_from": date_from})
    
    hotspots = []
    for row in result.all():
        import json
        centroid = json.loads(row[0])
        coords = centroid["coordinates"]
        categories = [IssueCategory(c) for c in row[2]]
        hotspots.append(HotspotData(
            coordinates=Coordinates(latitude=coords[1], longitude=coords[0]),
            count=row[1],
            categories=categories,
            avg_priority=round(row[3], 1),
            radius_meters=radius
        ))
    
    return hotspots


@router.get("/trends", response_model=TimeSeriesData)
async def get_trends(
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    days: int = Query(30, ge=7, le=365),
    category: Optional[IssueCategory] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    date_from = datetime.utcnow() - timedelta(days=days)
    
    if granularity == "day":
        date_trunc = func.date_trunc('day', Report.created_at)
    elif granularity == "week":
        date_trunc = func.date_trunc('week', Report.created_at)
    else:
        date_trunc = func.date_trunc('month', Report.created_at)
    
    query = select(
        date_trunc.label("period"),
        func.count(Report.id).label("count")
    ).where(Report.created_at >= date_from)
    
    if category:
        query = query.where(Report.category == category)
    
    query = query.group_by("period").order_by("period")
    
    result = await db.execute(query)
    
    series = [
        TimeSeriesPoint(date=row[0].isoformat(), count=row[1])
        for row in result.all()
    ]
    
    return TimeSeriesData(series=series, granularity=granularity)


@router.get("/priority-distribution")
async def get_priority_distribution(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Report.priority_band, func.count(Report.id))
        .where(Report.status.not_in([ReportStatus.REJECTED, ReportStatus.CLOSED]))
        .group_by(Report.priority_band)
    )
    
    return {row[0].value: row[1] for row in result.all()}


@router.get("/duplicate-rate")
async def get_duplicate_rate(
    db: AsyncSession = Depends(get_db)
):
    from app.models import DuplicateCandidate, DuplicateStatus
    
    total_result = await db.execute(select(func.count(Report.id)))
    total = total_result.scalar()
    
    dup_result = await db.execute(
        select(func.count(DuplicateCandidate.id)).where(DuplicateCandidate.status == DuplicateStatus.CONFIRMED)
    )
    confirmed = dup_result.scalar()
    
    return {
        "total_reports": total,
        "confirmed_duplicates": confirmed,
        "duplicate_rate": round(confirmed / total * 100, 1) if total > 0 else 0
    }