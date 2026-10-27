import os
import uuid
from datetime import datetime
from uagents import Agent, Context
from difflib import SequenceMatcher

from agents.common.messages import (
    DuplicateRequest, DuplicateResponse, DuplicateCandidate, AgentErrorResponse
)
from agents.common.schemas import IssueCategory


SEED = os.getenv("DUPLICATE_AGENT_SEED", "civicpulse-duplicate-agent-seed")
PORT = int(os.getenv("DUPLICATE_AGENT_PORT", "8002"))
ENDPOINT = os.getenv("DUPLICATE_AGENT_ENDPOINT", f"http://localhost:{PORT}/submit")

agent = Agent(
    name="duplicate-agent",
    seed=SEED,
    port=PORT,
    endpoint=[ENDPOINT],
)


MOCK_EXISTING_REPORTS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "tracking_id": "CP10000001",
        "category": IssueCategory.POTHOLE,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "description": "Large pothole on Main Street near City Mall",
        "created_at": "2024-01-10T10:00:00Z",
        "status": "verified",
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "tracking_id": "CP10000002",
        "category": IssueCategory.GARBAGE,
        "latitude": 12.9736,
        "longitude": 77.5976,
        "description": "Overflowing garbage bins at Central Park playground",
        "created_at": "2024-01-11T14:30:00Z",
        "status": "assigned",
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "tracking_id": "CP10000003",
        "category": IssueCategory.STREETLIGHT,
        "latitude": 12.9696,
        "longitude": 77.5926,
        "description": "Streetlight not working on Residential Lane for 3 days",
        "created_at": "2024-01-12T09:15:00Z",
        "status": "in_progress",
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "tracking_id": "CP10000004",
        "category": IssueCategory.WATER_LEAKAGE,
        "latitude": 12.9756,
        "longitude": 77.6006,
        "description": "Major water leakage on Commercial Road flooding shops",
        "created_at": "2024-01-13T16:45:00Z",
        "status": "resolved_pending_confirmation",
    },
]


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import radians, sin, cos, sqrt, atan2
    R = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def text_similarity(text1: str, text2: str) -> float:
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def calculate_match_score(distance: float, radius: int, category_match: bool, 
                         desc_similarity: float, time_proximity: float) -> float:
    distance_score = max(0, 1 - distance / radius)
    category_score = 1.0 if category_match else 0.3
    time_score = max(0, 1 - time_proximity / 168)
    return round(distance_score * 0.4 + category_score * 0.3 + desc_similarity * 0.2 + time_score * 0.1, 3)


def generate_explanation(distance: float, category_match: bool, desc_similarity: float, 
                        time_proximity: float, match_score: float) -> str:
    parts = [
        f"Distance: {distance:.0f}m",
        f"Category: {'match' if category_match else 'different'}",
        f"Description similarity: {desc_similarity:.0%}",
        f"Time difference: {time_proximity:.1f}h"
    ]
    return f"Match score {match_score:.0%}: " + "; ".join(parts)


@agent.on_message(model=DuplicateRequest)
async def handle_duplicate_detection(ctx: Context, sender: str, msg: DuplicateRequest):
    ctx.logger.info(f"Received duplicate detection request for report {msg.report_id}")
    
    try:
        radius = msg.radius_override or 100
        category = IssueCategory(msg.category)
        
        created_at = datetime.fromisoformat(msg.created_at.replace('Z', '+00:00')) if hasattr(msg, 'created_at') else datetime.utcnow()
        
        candidates = []
        for existing in MOCK_EXISTING_REPORTS:
            distance = calculate_distance(
                msg.latitude, msg.longitude,
                existing["latitude"], existing["longitude"]
            )
            
            if distance > radius:
                continue
            
            category_match = existing["category"] == category
            desc_sim = text_similarity(msg.description, existing["description"])
            time_proximity = abs((created_at - datetime.fromisoformat(existing["created_at"].replace('Z', '+00:00'))).total_seconds()) / 3600
            
            match_score = calculate_match_score(distance, radius, category_match, desc_sim, time_proximity)
            
            if match_score > 0.3:
                action = "confirm" if match_score > 0.8 else "review"
                explanation = generate_explanation(distance, category_match, desc_sim, time_proximity, match_score)
                
                candidates.append(DuplicateCandidate(
                    candidate_report_id=existing["id"],
                    candidate_tracking_id=existing["tracking_id"],
                    candidate_category=existing["category"].value,
                    distance_meters=round(distance, 1),
                    category_match=category_match,
                    description_similarity=round(desc_sim, 3),
                    image_similarity=None,
                    time_proximity_hours=round(time_proximity, 1),
                    match_score=match_score,
                    match_explanation=explanation,
                    suggested_action=action
                ))
        
        candidates.sort(key=lambda x: x.match_score, reverse=True)
        
        response = DuplicateResponse(
            report_id=msg.report_id,
            candidates=candidates[:10],
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"Sent duplicate response for report {msg.report_id}: {len(candidates)} candidates")
        
    except Exception as e:
        ctx.logger.error(f"Duplicate detection failed for report {msg.report_id}: {e}")
        error_response = AgentErrorResponse(
            report_id=msg.report_id,
            error_code="DUPLICATE_DETECTION_FAILED",
            error_message=str(e),
            retryable=True,
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        await ctx.send(sender, error_response)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Duplicate Agent started. Address: {agent.address}")


if __name__ == "__main__":
    agent.run()