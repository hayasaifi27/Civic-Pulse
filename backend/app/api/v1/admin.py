from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.core.database import get_db
from app.core.security import require_admin
from app.repositories import (
    CategoryRepository, DepartmentRepository, ServiceZoneRepository,
    RoutingRuleRepository, ScoringRuleRepository, AuditRepository
)
from app.schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    ServiceZoneCreate, ServiceZoneResponse,
    RoutingRuleCreate, RoutingRuleResponse,
    ScoringRuleCreate, ScoringRuleResponse
)
from app.models import ConfigurableCategory, Department, ServiceZone, RoutingRule, ScoringRule, AuditLog

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    repo = CategoryRepository(db)
    return await repo.get_all(active_only=active_only)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    repo = CategoryRepository(db)
    existing = await repo.get_by_code(category.code)
    if existing:
        raise HTTPException(status_code=400, detail="Category code already exists")
    return await repo.create(ConfigurableCategory(**category.model_dump()))


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    category: CategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    repo = CategoryRepository(db)
    updated = await repo.update(category_id, category.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    repo = DepartmentRepository(db)
    return await repo.get_all(active_only=active_only)


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department: DepartmentCreate,
    db: AsyncSession = Depends(get_db)
):
    repo = DepartmentRepository(db)
    existing = await repo.get_by_code(department.code)
    if existing:
        raise HTTPException(status_code=400, detail="Department code already exists")
    return await repo.create(Department(**department.model_dump()))


@router.patch("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: uuid.UUID,
    department: DepartmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    repo = DepartmentRepository(db)
    dept = await repo.get_by_id(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    for key, value in department.model_dump(exclude_unset=True).items():
        setattr(dept, key, value)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.get("/service-zones", response_model=List[ServiceZoneResponse])
async def list_service_zones(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    from app.repositories import ServiceZoneRepository
    repo = ServiceZoneRepository(db)
    return await repo.get_all(active_only=active_only)


@router.post("/service-zones", response_model=ServiceZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_service_zone(
    zone: ServiceZoneCreate,
    db: AsyncSession = Depends(get_db)
):
    from app.repositories import ServiceZoneRepository
    from geoalchemy2.shape import from_shape
    from shapely.geometry import shape
    
    repo = ServiceZoneRepository(db)
    geom = shape(zone.boundary)
    db_zone = ServiceZone(
        name=zone.name,
        code=zone.code,
        boundary=from_shape(geom, srid=4326),
        description=zone.description
    )
    return await repo.create(db_zone)


@router.get("/routing-rules", response_model=List[RoutingRuleResponse])
async def list_routing_rules(
    category_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    from app.repositories import RoutingRuleRepository
    repo = RoutingRuleRepository(db)
    return await repo.get_all(category_id=category_id)


@router.post("/routing-rules", response_model=RoutingRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_routing_rule(
    rule: RoutingRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    from app.repositories import RoutingRuleRepository
    repo = RoutingRuleRepository(db)
    return await repo.create(RoutingRule(**rule.model_dump()))


@router.get("/scoring-rules", response_model=List[ScoringRuleResponse])
async def list_scoring_rules(
    db: AsyncSession = Depends(get_db)
):
    from app.repositories import ScoringRuleRepository
    repo = ScoringRuleRepository(db)
    return await repo.get_all()


@router.post("/scoring-rules", response_model=ScoringRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_scoring_rule(
    rule: ScoringRuleCreate,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.repositories import ScoringRuleRepository
    repo = ScoringRuleRepository(db)
    db_rule = ScoringRule(**rule.model_dump(), created_by=current_user.id)
    return await repo.create(db_rule)


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    actor_id: Optional[uuid.UUID] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime
    from app.repositories import AuditRepository
    
    repo = AuditRepository(db)
    return await repo.get_logs(
        page=page,
        page_size=page_size,
        actor_id=actor_id,
        resource_type=resource_type,
        action=action,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/users")
async def list_users(
    role: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    from app.repositories import ProfileRepository
    from app.models import UserRole
    
    repo = ProfileRepository(db)
    user_role = UserRole(role) if role else None
    return await repo.get_by_role(user_role, limit=page_size, offset=(page-1)*page_size) if user_role else await repo.get_all(limit=page_size, offset=(page-1)*page_size)