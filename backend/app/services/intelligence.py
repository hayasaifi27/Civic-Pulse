from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from app.schemas import (
    ClassificationResult, VerificationResult, PriorityScoreResult,
    RoutingRecommendation, Coordinates, IssueCategory
)
from app.models import Report, ConfigurableCategory, Department, ReportStatus


class VisionProvider(ABC):
    @abstractmethod
    async def analyze_image(
        self,
        image_url: str,
        description: str,
        category_hint: Optional[IssueCategory] = None
    ) -> ClassificationResult:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class MockVisionProvider(VisionProvider):
    def __init__(self):
        self.category_keywords = {
            IssueCategory.POTHOLE: ["pothole", "hole", "road damage", "crack", "asphalt", "pavement"],
            IssueCategory.GARBAGE: ["garbage", "trash", "waste", "rubbish", "overflow", "bin", "litter"],
            IssueCategory.STREETLIGHT: ["streetlight", "light", "lamp", "dark", "broken light", "outage"],
            IssueCategory.WATER_LEAKAGE: ["water", "leak", "pipe", "burst", "flood", "leaking"],
            IssueCategory.DRAINAGE: ["drain", "blocked", "clogged", "sewer", "flood", "water logging"],
            IssueCategory.FOOTPATH: ["footpath", "sidewalk", "pavement", "cracked", "uneven", "broken"],
            IssueCategory.OBSTRUCTION: ["obstruction", "blocked", "debris", "fallen", "tree", "blocking"],
            IssueCategory.PROPERTY_DAMAGE: ["damage", "broken", "vandal", "graffiti", "destroyed"],
            IssueCategory.SANITATION: ["sanitation", "toilet", "sewage", "smell", "odor", "hygiene"],
        }

    async def analyze_image(
        self,
        image_url: str,
        description: str,
        category_hint: Optional[IssueCategory] = None
    ) -> ClassificationResult:
        desc_lower = description.lower()
        scores = {}
        
        for cat, keywords in self.category_keywords.items():
            score = sum(1 for kw in keywords if kw in desc_lower)
            if score > 0:
                scores[cat] = score
        
        if category_hint and category_hint in scores:
            scores[category_hint] += 2

        if scores:
            predicted = max(scores, key=scores.get)
            confidence = min(0.9, 0.5 + scores[predicted] * 0.1)
        else:
            predicted = IssueCategory.OTHER
            confidence = 0.3

        alternatives = [
            {"category": cat, "confidence": min(0.8, confidence - 0.1 * i)}
            for i, cat in enumerate(sorted(scores, key=scores.get, reverse=True)[1:4])
        ]

        evidence_quality = "good" if confidence > 0.7 else "fair" if confidence > 0.5 else "poor"
        needs_review = confidence < 0.7

        return ClassificationResult(
            predicted_category=predicted,
            confidence=confidence,
            alternatives=alternatives,
            explanation=f"Mock analysis based on text description. Keywords matched: {', '.join(self.category_keywords.get(predicted, []))}",
            evidence_quality=evidence_quality,
            needs_human_review=needs_review,
            model_version="mock-v1.0",
            is_mock=True
        )

    def is_available(self) -> bool:
        return True


class OpenAIVisionProvider(VisionProvider):
    def __init__(self, api_key: str, model: str = "gpt-4-vision-preview"):
        self.api_key = api_key
        self.model = model
        self.client = None

    def _get_client(self):
        if self.client is None:
            import openai
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        return self.client

    async def analyze_image(
        self,
        image_url: str,
        description: str,
        category_hint: Optional[IssueCategory] = None
    ) -> ClassificationResult:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        client = self._get_client()
        
        categories = [c.value for c in IssueCategory]
        prompt = f"""Analyze this civic issue image and description. Classify into one of these categories: {', '.join(categories)}.
        
Description: {description}
{f'Suggested category: {category_hint.value}' if category_hint else ''}

Return JSON with: category, confidence (0-1), alternatives (list of {{category, confidence}}), explanation, evidence_quality (good/fair/poor), needs_human_review (boolean)."""

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a civic issue classification assistant. Return valid JSON only."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            import json
            content = response.choices[0].message.content
            data = json.loads(content)
            
            return ClassificationResult(
                predicted_category=IssueCategory(data["category"]),
                confidence=data["confidence"],
                alternatives=data.get("alternatives", []),
                explanation=data["explanation"],
                evidence_quality=data["evidence_quality"],
                needs_human_review=data["needs_human_review"],
                model_version=self.model,
                is_mock=False
            )
        except Exception as e:
            return ClassificationResult(
                predicted_category=IssueCategory.OTHER,
                confidence=0.1,
                alternatives=[],
                explanation=f"Analysis failed: {str(e)}",
                evidence_quality="poor",
                needs_human_review=True,
                model_version=self.model,
                is_mock=False
            )

    def is_available(self) -> bool:
        return bool(self.api_key)


def get_vision_provider() -> VisionProvider:
    from app.core.config import settings
    if settings.vision_provider == "openai" and settings.vision_api_key:
        return OpenAIVisionProvider(settings.vision_api_key, settings.vision_model)
    return MockVisionProvider()


class ClassificationService:
    def __init__(self, vision_provider: Optional[VisionProvider] = None):
        self.vision_provider = vision_provider or get_vision_provider()

    async def classify_report(
        self,
        report: Report,
        media_urls: List[str],
        category_hint: Optional[IssueCategory] = None
    ) -> ClassificationResult:
        description = report.description
        if report.title:
            description = f"{report.title}. {description}"

        primary_image = media_urls[0] if media_urls else ""
        
        if not primary_image:
            return ClassificationResult(
                predicted_category=category_hint or IssueCategory.OTHER,
                confidence=0.3,
                alternatives=[],
                explanation="No image provided for analysis",
                evidence_quality="poor",
                needs_human_review=True,
                model_version="mock-v1.0",
                is_mock=True
            )

        return await self.vision_provider.analyze_image(
            primary_image, description, category_hint
        )


class VerificationService:
    def __init__(self, max_file_size: int = 10485760):
        self.max_file_size = max_file_size
        self.allowed_types = {"image/jpeg", "image/png", "image/webp", "image/heic"}

    async def verify_report(
        self,
        report: Report,
        media: List[Dict[str, Any]],
        classification: ClassificationResult
    ) -> VerificationResult:
        issues = []
        missing_fields = []

        if not report.description or len(report.description.strip()) < 10:
            missing_fields.append("description")

        if not report.coordinates:
            missing_fields.append("coordinates")

        if not media:
            issues.append("No media attached")
        else:
            for m in media:
                if m.get("file_size", 0) > self.max_file_size:
                    issues.append(f"File {m.get('file_name')} exceeds size limit")
                if m.get("mime_type") not in self.allowed_types:
                    issues.append(f"File {m.get('file_name')} has unsupported type")

        if classification.needs_human_review:
            issues.append("Classification confidence low, needs human review")

        if classification.evidence_quality == "poor":
            issues.append("Evidence quality assessed as poor")

        if missing_fields:
            return VerificationResult(
                status="needs_info",
                missing_fields=missing_fields,
                evidence_quality=classification.evidence_quality,
                review_recommendation="Provide missing information",
                issues=issues
            )

        if issues:
            return VerificationResult(
                status="needs_review",
                missing_fields=[],
                evidence_quality=classification.evidence_quality,
                review_recommendation="Review required due to issues",
                issues=issues
            )

        return VerificationResult(
            status="valid",
            missing_fields=[],
            evidence_quality=classification.evidence_quality,
            review_recommendation="Ready for processing",
            issues=[]
        )


class DuplicateDetectionService:
    def __init__(self, db_session):
        self.db = db_session

    async def find_candidates(
        self,
        report: Report,
        media_features: Optional[Dict[str, Any]] = None,
        radius_override: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        from app.repositories import ReportRepository, CategoryRepository
        
        report_repo = ReportRepository(self.db)
        cat_repo = CategoryRepository(self.db)
        
        category_config = await cat_repo.get_by_code(report.category.value)
        radius = radius_override or (category_config.duplicate_distance_meters if category_config else 100)

        nearby = await report_repo.find_nearby(
            Coordinates(latitude=report.coordinates.y, longitude=report.coordinates.x),
            category=report.category,
            radius_meters=radius,
            exclude_id=report.id,
            status_filter=[ReportStatus.REPORTED, ReportStatus.UNDER_REVIEW, ReportStatus.VERIFIED, ReportStatus.ASSIGNED, ReportStatus.IN_PROGRESS],
            limit=20
        )

        candidates = []
        for existing in nearby:
            distance = self._calculate_distance(report, existing)
            category_match = existing.category == report.category
            desc_similarity = self._text_similarity(report.description, existing.description)
            time_proximity = abs((report.created_at - existing.created_at).total_seconds()) / 3600
            
            match_score = self._calculate_match_score(
                distance, radius, category_match, desc_similarity, time_proximity
            )

            if match_score > 0.3:
                action = "confirm" if match_score > 0.8 else "review"
                explanation = self._generate_explanation(
                    distance, category_match, desc_similarity, time_proximity, match_score
                )
                
                candidates.append({
                    "candidate_report_id": existing.id,
                    "candidate_tracking_id": existing.tracking_id,
                    "candidate_title": existing.title,
                    "candidate_category": existing.category,
                    "candidate_coordinates": Coordinates(latitude=existing.coordinates.y, longitude=existing.coordinates.x),
                    "candidate_status": existing.status,
                    "distance_meters": distance,
                    "category_match": category_match,
                    "description_similarity": desc_similarity,
                    "image_similarity": None,
                    "time_proximity_hours": time_proximity,
                    "match_score": match_score,
                    "match_explanation": explanation,
                    "suggested_action": action
                })

        candidates.sort(key=lambda x: x["match_score"], reverse=True)
        return candidates[:10]

    def _calculate_distance(self, report1: Report, report2: Report) -> float:
        from geoalchemy2.shape import to_shape
        p1 = to_shape(report1.coordinates)
        p2 = to_shape(report2.coordinates)
        from geopy.distance import geodesic
        return geodesic((p1.y, p1.x), (p2.y, p2.x)).meters

    def _text_similarity(self, text1: str, text2: str) -> float:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _calculate_match_score(
        self,
        distance: float,
        radius: int,
        category_match: bool,
        desc_similarity: float,
        time_proximity: float
    ) -> float:
        distance_score = max(0, 1 - distance / radius)
        category_score = 1.0 if category_match else 0.3
        time_score = max(0, 1 - time_proximity / 168)
        
        return (distance_score * 0.4 + category_score * 0.3 + desc_similarity * 0.2 + time_score * 0.1)

    def _generate_explanation(
        self,
        distance: float,
        category_match: bool,
        desc_similarity: float,
        time_proximity: float,
        match_score: float
    ) -> str:
        parts = []
        parts.append(f"Distance: {distance:.0f}m")
        parts.append(f"Category: {'match' if category_match else 'different'}")
        parts.append(f"Description similarity: {desc_similarity:.0%}")
        parts.append(f"Time difference: {time_proximity:.1f}h")
        return f"Match score {match_score:.0%}: " + "; ".join(parts)


class PriorityScoringService:
    def __init__(self, db_session):
        self.db = db_session

    async def calculate_priority(
        self,
        report: Report,
        duplicate_count: int = 0,
        rule_version: str = "v1.0"
    ) -> PriorityScoreResult:
        from app.repositories import PriorityRepository
        
        repo = PriorityRepository(self.db)
        rule = await repo.get_active_rule()
        
        if rule:
            weights = {
                "severity": rule.severity_weight,
                "risk": rule.risk_weight,
                "time": rule.time_weight,
                "corroboration": rule.corroboration_weight
            }
            escalation_threshold = rule.safety_escalation_threshold
        else:
            weights = {"severity": 0.35, "risk": 0.25, "time": 0.20, "corroboration": 0.20}
            escalation_threshold = 85.0

        severity = await self._calculate_severity(report)
        risk = await self._calculate_risk(report)
        time_score = self._calculate_time_score(report)
        corroboration = min(100, duplicate_count * 15 + 10)

        total = (
            severity * weights["severity"] +
            risk * weights["risk"] +
            time_score * weights["time"] +
            corroboration * weights["corroboration"]
        )

        band = self._score_to_band(total)
        escalation = total >= escalation_threshold
        escalation_reason = "Priority score exceeds safety escalation threshold" if escalation else None

        return PriorityScoreResult(
            priority_score=round(total, 1),
            priority_band=band,
            severity_score=round(severity, 1),
            risk_score=round(risk, 1),
            time_score=round(time_score, 1),
            corroboration_score=round(corroboration, 1),
            factor_details={
                "weights": weights,
                "severity_factors": await self._get_severity_factors(report),
                "risk_factors": await self._get_risk_factors(report),
                "time_unresolved_hours": (datetime.utcnow() - report.created_at).total_seconds() / 3600,
                "duplicate_count": duplicate_count
            },
            escalation_recommended=escalation,
            escalation_reason=escalation_reason,
            rule_version=rule_version
        )

    async def _calculate_severity(self, report: Report) -> float:
        base_scores = {
            IssueCategory.POTHOLE: 70,
            IssueCategory.GARBAGE: 50,
            IssueCategory.STREETLIGHT: 60,
            IssueCategory.WATER_LEAKAGE: 80,
            IssueCategory.DRAINAGE: 75,
            IssueCategory.FOOTPATH: 55,
            IssueCategory.OBSTRUCTION: 85,
            IssueCategory.PROPERTY_DAMAGE: 65,
            IssueCategory.SANITATION: 70,
            IssueCategory.OTHER: 40
        }
        base = base_scores.get(report.category, 40)
        
        from app.repositories import CategoryRepository
        cat_repo = CategoryRepository(self.db)
        cat_config = await cat_repo.get_by_code(report.category.value)
        if cat_config:
            base = cat_config.severity_base
        
        return min(100, base + (report.priority_score or 0) * 0.1)

    async def _calculate_risk(self, report: Report) -> float:
        base_scores = {
            IssueCategory.POTHOLE: 65,
            IssueCategory.GARBAGE: 45,
            IssueCategory.STREETLIGHT: 55,
            IssueCategory.WATER_LEAKAGE: 75,
            IssueCategory.DRAINAGE: 70,
            IssueCategory.FOOTPATH: 50,
            IssueCategory.OBSTRUCTION: 90,
            IssueCategory.PROPERTY_DAMAGE: 55,
            IssueCategory.SANITATION: 60,
            IssueCategory.OTHER: 35
        }
        base = base_scores.get(report.category, 35)
        
        from app.repositories import CategoryRepository
        cat_repo = CategoryRepository(self.db)
        cat_config = await cat_repo.get_by_code(report.category.value)
        if cat_config:
            base = cat_config.risk_base
        
        return min(100, base)

    def _calculate_time_score(self, report: Report) -> float:
        hours = (datetime.utcnow() - report.created_at).total_seconds() / 3600
        if hours < 24:
            return hours / 24 * 30
        elif hours < 168:
            return 30 + (hours - 24) / 144 * 40
        else:
            return min(100, 70 + (hours - 168) / 168 * 30)

    def _score_to_band(self, score: float) -> PriorityBand:
        if score >= 80:
            return PriorityBand.CRITICAL
        elif score >= 60:
            return PriorityBand.HIGH
        elif score >= 35:
            return PriorityBand.MEDIUM
        return PriorityBand.LOW

    async def _get_severity_factors(self, report: Report) -> Dict[str, Any]:
        return {"category_base": await self._calculate_severity(report)}

    async def _get_risk_factors(self, report: Report) -> Dict[str, Any]:
        return {"category_base": await self._calculate_risk(report)}


class RoutingService:
    def __init__(self, db_session):
        self.db = db_session

    async def recommend_department(
        self,
        report: Report,
        priority_band: PriorityBand
    ) -> RoutingRecommendation:
        from app.repositories import DepartmentRepository, RoutingRule
        from sqlalchemy import select
        
        query = select(RoutingRule).where(
            RoutingRule.category_id == report.category,
            RoutingRule.is_active == True
        )
        
        if report.coordinates:
            query = query.where(
                or_(
                    RoutingRule.service_zone_id.is_(None),
                    RoutingRule.service_zone.has(ServiceZone.boundary.ST_Contains(report.coordinates))
                )
            )
        
        if priority_band in [PriorityBand.CRITICAL, PriorityBand.SAFETY_ESCALATION]:
            query = query.where(
                or_(
                    RoutingRule.priority_band.is_(None),
                    RoutingRule.priority_band == priority_band
                )
            )
        
        query = query.order_by(RoutingRule.is_default.desc())
        result = await self.db.execute(query)
        rule = result.scalars().first()
        
        if rule:
            dept_repo = DepartmentRepository(self.db)
            dept = await dept_repo.get_by_id(rule.department_id)
            if dept:
                return RoutingRecommendation(
                    department_id=dept.id,
                    department_name=dept.name,
                    queue=rule.priority_band.value if rule.priority_band else "standard",
                    reason=f"Routing rule matched: category={report.category.value}, zone={rule.service_zone_id or 'any'}",
                    needs_manual_review=False
                )

        default_depts = {
            IssueCategory.POTHOLE: "roads",
            IssueCategory.GARBAGE: "sanitation",
            IssueCategory.STREETLIGHT: "electrical",
            IssueCategory.WATER_LEAKAGE: "water_supply",
            IssueCategory.DRAINAGE: "drainage",
            IssueCategory.FOOTPATH: "roads",
            IssueCategory.OBSTRUCTION: "roads",
            IssueCategory.PROPERTY_DAMAGE: "public_works",
            IssueCategory.SANITATION: "sanitation",
            IssueCategory.OTHER: "general"
        }
        
        dept_code = default_depts.get(report.category, "general")
        dept_repo = DepartmentRepository(self.db)
        dept = await dept_repo.get_by_code(dept_code)
        
        if not dept:
            depts = await dept_repo.get_all()
            dept = depts[0] if depts else None
        
        if dept:
            return RoutingRecommendation(
                department_id=dept.id,
                department_name=dept.name,
                queue="standard",
                reason=f"Default routing for category {report.category.value}",
                needs_manual_review=True
            )
        
        raise ValueError("No departments configured")