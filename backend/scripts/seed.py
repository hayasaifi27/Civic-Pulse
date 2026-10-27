import asyncio
import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shapely.geometry import Point, Polygon, mapping

from app.core.database import async_session_maker, init_db
from app.models import (
    Profile, Department, ServiceZone, ConfigurableCategory, RoutingRule, ScoringRule,
    Report, ReportMedia, ReportEvent, ReportStatus, IssueCategory, PriorityBand,
    UserRole, Assignment, AssignmentStatus, ResolutionEvidence, ResolutionStatus
)
from app.core.security import get_password_hash


async def seed_data():
    async with async_session_maker() as db:
        print("Seeding database...")
        
        dept_data = [
            {"name": "Roads Department", "code": "roads", "description": "Road maintenance and repair", "contact_email": "roads@city.gov", "sla_hours": 72},
            {"name": "Sanitation Department", "code": "sanitation", "description": "Garbage collection and sanitation", "contact_email": "sanitation@city.gov", "sla_hours": 48},
            {"name": "Electrical Department", "code": "electrical", "description": "Street lighting and electrical", "contact_email": "electrical@city.gov", "sla_hours": 72},
            {"name": "Water Supply Department", "code": "water_supply", "description": "Water supply and leakage", "contact_email": "water@city.gov", "sla_hours": 48},
            {"name": "Drainage Department", "code": "drainage", "description": "Storm water drainage", "contact_email": "drainage@city.gov", "sla_hours": 72},
            {"name": "Public Works", "code": "public_works", "description": "General public infrastructure", "contact_email": "publicworks@city.gov", "sla_hours": 96},
        ]
        
        departments = {}
        for d in dept_data:
            dept = Department(**d)
            db.add(dept)
            await db.flush()
            departments[d["code"]] = dept
        
        print(f"Created {len(departments)} departments")
        
        city_boundary = Polygon([
            (77.5, 12.9), (77.7, 12.9), (77.7, 13.1), (77.5, 13.1), (77.5, 12.9)
        ])
        
        zones = [
            {"name": "North Zone", "code": "north", "boundary": json.dumps(mapping(Polygon([(77.5, 13.0), (77.7, 13.0), (77.7, 13.1), (77.5, 13.1), (77.5, 13.0)])))},
            {"name": "South Zone", "code": "south", "boundary": json.dumps(mapping(Polygon([(77.5, 12.9), (77.7, 12.9), (77.7, 13.0), (77.5, 13.0), (77.5, 12.9)])))},
            {"name": "Central Zone", "code": "central", "boundary": json.dumps(mapping(Polygon([(77.55, 12.95), (77.65, 12.95), (77.65, 13.05), (77.55, 13.05), (77.55, 12.95)])))},
        ]
        
        service_zones = {}
        for z in zones:
            zone = ServiceZone(**z)
            db.add(zone)
            await db.flush()
            service_zones[z["code"]] = zone
        
        print(f"Created {len(service_zones)} service zones")
        
        categories = [
            {"code": "pothole", "name": "Pothole / Road Damage", "description": "Potholes, cracks, and road surface damage", "icon": "road", "color": "#E74C3C", "severity_base": 70, "risk_base": 65, "department_id": departments["roads"].id, "sla_hours": 72, "duplicate_distance_meters": 100, "sort_order": 1},
            {"code": "garbage", "name": "Garbage Accumulation", "description": "Overflowing bins, illegal dumping, litter", "icon": "trash", "color": "#F39C12", "severity_base": 50, "risk_base": 45, "department_id": departments["sanitation"].id, "sla_hours": 48, "duplicate_distance_meters": 50, "sort_order": 2},
            {"code": "streetlight", "name": "Broken Streetlight", "description": "Non-functional or damaged street lights", "icon": "lightbulb", "color": "#F1C40F", "severity_base": 60, "risk_base": 55, "department_id": departments["electrical"].id, "sla_hours": 72, "duplicate_distance_meters": 30, "sort_order": 3},
            {"code": "water_leakage", "name": "Water Leakage", "description": "Pipe bursts, leaking mains, water wastage", "icon": "droplet", "color": "#3498DB", "severity_base": 80, "risk_base": 75, "department_id": departments["water_supply"].id, "sla_hours": 48, "duplicate_distance_meters": 100, "sort_order": 4},
            {"code": "drainage", "name": "Drainage Blockage", "description": "Blocked drains, water logging, sewer issues", "icon": "filter", "color": "#2C3E50", "severity_base": 75, "risk_base": 70, "department_id": departments["drainage"].id, "sla_hours": 72, "duplicate_distance_meters": 100, "sort_order": 5},
            {"code": "footpath", "name": "Damaged Footpath", "description": "Cracked, uneven, or broken sidewalks", "icon": "footprints", "color": "#95A5A6", "severity_base": 55, "risk_base": 50, "department_id": departments["roads"].id, "sla_hours": 96, "duplicate_distance_meters": 50, "sort_order": 6},
            {"code": "obstruction", "name": "Unsafe Road Obstruction", "description": "Fallen trees, debris, construction hazards", "icon": "alert-triangle", "color": "#C0392B", "severity_base": 85, "risk_base": 90, "department_id": departments["roads"].id, "sla_hours": 24, "duplicate_distance_meters": 100, "sort_order": 7},
            {"code": "property_damage", "name": "Public Property Damage", "description": "Vandalism, broken fixtures, damaged amenities", "icon": "hammer", "color": "#8E44AD", "severity_base": 65, "risk_base": 55, "department_id": departments["public_works"].id, "sla_hours": 96, "duplicate_distance_meters": 50, "sort_order": 8},
            {"code": "sanitation", "name": "Sanitation Concern", "description": "Public toilet issues, sewage, hygiene", "icon": "shield", "color": "#27AE60", "severity_base": 70, "risk_base": 60, "department_id": departments["sanitation"].id, "sla_hours": 48, "duplicate_distance_meters": 50, "sort_order": 9},
            {"code": "other", "name": "Other / Uncertain", "description": "Issues not fitting other categories", "icon": "help-circle", "color": "#7F8C8D", "severity_base": 40, "risk_base": 35, "department_id": departments["public_works"].id, "sla_hours": 96, "duplicate_distance_meters": 100, "sort_order": 10},
        ]
        
        category_objects = {}
        for c in categories:
            cat = ConfigurableCategory(**c)
            db.add(cat)
            await db.flush()
            category_objects[c["code"]] = cat
        
        print(f"Created {len(category_objects)} categories")
        
        routing_rules = [
            {"category_id": category_objects["pothole"].id, "department_id": departments["roads"].id, "is_default": True},
            {"category_id": category_objects["garbage"].id, "department_id": departments["sanitation"].id, "is_default": True},
            {"category_id": category_objects["streetlight"].id, "department_id": departments["electrical"].id, "is_default": True},
            {"category_id": category_objects["water_leakage"].id, "department_id": departments["water_supply"].id, "is_default": True},
            {"category_id": category_objects["drainage"].id, "department_id": departments["drainage"].id, "is_default": True},
            {"category_id": category_objects["footpath"].id, "department_id": departments["roads"].id, "is_default": True},
            {"category_id": category_objects["obstruction"].id, "department_id": departments["roads"].id, "is_default": True},
            {"category_id": category_objects["property_damage"].id, "department_id": departments["public_works"].id, "is_default": True},
            {"category_id": category_objects["sanitation"].id, "department_id": departments["sanitation"].id, "is_default": True},
            {"category_id": category_objects["other"].id, "department_id": departments["public_works"].id, "is_default": True},
        ]
        
        for r in routing_rules:
            rule = RoutingRule(**r)
            db.add(rule)
        
        print("Created routing rules")
        
        scoring_rule = ScoringRule(
            version="v1.0",
            severity_weight=0.35,
            risk_weight=0.25,
            time_weight=0.20,
            corroboration_weight=0.20,
            safety_escalation_threshold=85.0,
            is_active=True,
            description="Initial scoring rule"
        )
        db.add(scoring_rule)
        
        print("Created scoring rule")
        
        admin_user = Profile(
            email="admin@civicpulse.local",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            hashed_password=get_password_hash("admin123")
        )
        db.add(admin_user)
        
        field_worker = Profile(
            email="worker@civicpulse.local",
            full_name="Field Worker",
            role=UserRole.FIELD_WORKER,
            is_active=True,
            is_verified=True,
            department_id=departments["roads"].id,
            hashed_password=get_password_hash("worker123")
        )
        db.add(field_worker)
        
        supervisor = Profile(
            email="supervisor@civicpulse.local",
            full_name="Supervisor",
            role=UserRole.SUPERVISOR,
            is_active=True,
            is_verified=True,
            department_id=departments["roads"].id,
            hashed_password=get_password_hash("supervisor123")
        )
        db.add(supervisor)
        
        citizen = Profile(
            email="citizen@civicpulse.local",
            full_name="Test Citizen",
            role=UserRole.CITIZEN,
            is_active=True,
            is_verified=True,
            hashed_password=get_password_hash("citizen123")
        )
        db.add(citizen)
        
        await db.flush()
        print("Created users")
        
        sample_reports = [
            {
                "title": "Large pothole on Main Street",
                "description": "Deep pothole near the intersection of Main St and 1st Ave. Causing traffic hazards and vehicle damage. Approximately 2 feet wide and 6 inches deep.",
                "category": IssueCategory.POTHOLE,
                "coordinates": Point(77.5946, 12.9716),
                "address": "Main Street & 1st Ave",
                "landmark": "Near City Mall",
                "reporter_id": citizen.id,
                "status": ReportStatus.VERIFIED,
                "priority_score": 78.5,
                "priority_band": PriorityBand.HIGH,
            },
            {
                "title": "Overflowing garbage bins at Central Park",
                "description": "Multiple garbage bins overflowing near the playground area. Strong odor and attracting pests. Needs urgent cleanup.",
                "category": IssueCategory.GARBAGE,
                "coordinates": Point(77.5976, 12.9736),
                "address": "Central Park Entrance",
                "landmark": "Near Playground",
                "reporter_id": citizen.id,
                "status": ReportStatus.ASSIGNED,
                "priority_score": 62.0,
                "priority_band": PriorityBand.MEDIUM,
            },
            {
                "title": "Streetlight not working on Residential Lane",
                "description": "Streetlight has been out for 3 days. Very dark at night, safety concern for pedestrians.",
                "category": IssueCategory.STREETLIGHT,
                "coordinates": Point(77.5926, 12.9696),
                "address": "Residential Lane, House 45",
                "landmark": "Near Community Center",
                "reporter_id": citizen.id,
                "status": ReportStatus.IN_PROGRESS,
                "priority_score": 55.0,
                "priority_band": PriorityBand.MEDIUM,
            },
            {
                "title": "Major water leakage on Commercial Road",
                "description": "Water gushing from underground pipe. Flooding the road and nearby shops. Urgent attention needed.",
                "category": IssueCategory.WATER_LEAKAGE,
                "coordinates": Point(77.6006, 12.9756),
                "address": "Commercial Road, Block A",
                "landmark": "Opposite Metro Station",
                "reporter_id": citizen.id,
                "status": ReportStatus.RESOLVED_PENDING_CONFIRMATION,
                "priority_score": 88.0,
                "priority_band": PriorityBand.CRITICAL,
            },
            {
                "title": "Blocked drain causing water logging",
                "description": "Storm drain completely blocked after heavy rains. Water logging up to 2 feet on the road. Traffic disrupted.",
                "category": IssueCategory.DRAINAGE,
                "coordinates": Point(77.5886, 12.9676),
                "address": "Lake View Road",
                "landmark": "Near Lake",
                "reporter_id": citizen.id,
                "status": ReportStatus.CLOSED,
                "priority_score": 72.0,
                "priority_band": PriorityBand.HIGH,
            },
            {
                "title": "Cracked footpath near School",
                "description": "Footpath severely cracked and uneven near the primary school. Children and elderly having difficulty walking.",
                "category": IssueCategory.FOOTPATH,
                "coordinates": Point(77.5966, 12.9726),
                "address": "School Road",
                "landmark": "Near Primary School",
                "reporter_id": citizen.id,
                "status": ReportStatus.UNDER_REVIEW,
                "priority_score": 58.0,
                "priority_band": PriorityBand.MEDIUM,
            },
            {
                "title": "Fallen tree blocking road after storm",
                "description": "Large tree fallen across both lanes after yesterday's storm. Completely blocking traffic. Emergency hazard.",
                "category": IssueCategory.OBSTRUCTION,
                "coordinates": Point(77.5906, 12.9706),
                "address": "Highway Access Road",
                "landmark": "Near Bridge",
                "reporter_id": citizen.id,
                "status": ReportStatus.ASSIGNED,
                "priority_score": 92.0,
                "priority_band": PriorityBand.SAFETY_ESCALATION,
            },
            {
                "title": "Broken bench in Community Park",
                "description": "Park bench completely broken, sharp metal edges exposed. Safety hazard for park visitors.",
                "category": IssueCategory.PROPERTY_DAMAGE,
                "coordinates": Point(77.5996, 12.9746),
                "address": "Community Park",
                "landmark": "Near Fountain",
                "reporter_id": citizen.id,
                "status": ReportStatus.REPORTED,
                "priority_score": 45.0,
                "priority_band": PriorityBand.LOW,
            },
        ]
        
        report_objects = {}
        for i, r in enumerate(sample_reports):
            report = Report(
                tracking_id=f"CP{10000000 + i}",
                title=r["title"],
                description=r["description"],
                category=r["category"],
                coordinates=json.dumps({"type": "Point", "coordinates": [r["coordinates"].x, r["coordinates"].y]}),
                address=r["address"],
                landmark=r["landmark"],
                reporter_id=r["reporter_id"],
                status=r["status"],
                priority_score=r["priority_score"],
                priority_band=r["priority_band"],
                priority_version="v1.0",
                assigned_department_id=category_objects[r["category"].value].department_id,
                created_at=datetime.utcnow() - timedelta(days=len(sample_reports) - i),
                updated_at=datetime.utcnow() - timedelta(days=len(sample_reports) - i),
            )
            db.add(report)
            await db.flush()
            report_objects[r["category"].value] = report
        
        print(f"Created {len(report_objects)} sample reports")
        
        for cat_code, report in report_objects.items():
            event = ReportEvent(
                report_id=report.id,
                event_type="created",
                new_status=ReportStatus.REPORTED,
                actor_id=citizen.id,
                actor_role=UserRole.CITIZEN,
                reason="Report submitted by citizen"
            )
            db.add(event)
            
            if report.status != ReportStatus.REPORTED:
                event = ReportEvent(
                    report_id=report.id,
                    event_type="status_change",
                    previous_status=ReportStatus.REPORTED,
                    new_status=report.status,
                    actor_id=admin_user.id,
                    actor_role=UserRole.ADMIN,
                    reason=f"Status updated to {report.status.value}"
                )
                db.add(event)
        
        for cat_code in ["pothole", "garbage", "streetlight", "water_leakage"]:
            report = report_objects[cat_code]
            assignment = Assignment(
                report_id=report.id,
                department_id=report.assigned_department_id,
                worker_id=field_worker.id if cat_code in ["pothole", "footpath"] else None,
                assigned_by=admin_user.id,
                status=AssignmentStatus.ACCEPTED if report.status in [ReportStatus.ASSIGNED, ReportStatus.IN_PROGRESS, ReportStatus.RESOLVED_PENDING_CONFIRMATION, ReportStatus.CLOSED] else AssignmentStatus.PENDING,
                instructions="Please inspect and resolve as per department guidelines",
                sla_deadline=datetime.utcnow() + timedelta(hours=72),
                accepted_at=datetime.utcnow() - timedelta(days=1) if report.status != ReportStatus.ASSIGNED else None,
                started_at=datetime.utcnow() - timedelta(hours=12) if report.status == ReportStatus.IN_PROGRESS else None,
                completed_at=datetime.utcnow() - timedelta(hours=2) if report.status in [ReportStatus.RESOLVED_PENDING_CONFIRMATION, ReportStatus.CLOSED] else None,
            )
            db.add(assignment)
            await db.flush()
            
            if report.status in [ReportStatus.RESOLVED_PENDING_CONFIRMATION, ReportStatus.CLOSED]:
                resolution = ResolutionEvidence(
                    report_id=report.id,
                    assignment_id=assignment.id,
                    submitted_by_id=field_worker.id,
                    before_media=[{"url": f"/media/before_{cat_code}.jpg", "caption": "Before repair"}],
                    after_media=[{"url": f"/media/after_{cat_code}.jpg", "caption": "After repair"}],
                    work_notes=f"Completed repair work for {cat_code} issue",
                    status=ResolutionStatus.APPROVED if report.status == ReportStatus.CLOSED else ResolutionStatus.SUBMITTED,
                    reviewed_by=supervisor.id if report.status == ReportStatus.CLOSED else None,
                    reviewed_at=datetime.utcnow() - timedelta(hours=1) if report.status == ReportStatus.CLOSED else None,
                )
                db.add(resolution)
        
        print("Created assignments and resolutions")
        
        await db.commit()
        print("Seeding completed!")


if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(seed_data())