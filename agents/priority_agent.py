import os
import uuid
from datetime import datetime
from uagents import Agent, Context

from agents.common.messages import (
    PriorityRequest, PriorityResponse, AgentErrorResponse
)
from agents.common.schemas import IssueCategory, PriorityBand


SEED = os.getenv("PRIORITY_AGENT_SEED", "civicpulse-priority-agent-seed")
PORT = int(os.getenv("PRIORITY_AGENT_PORT", "8003"))
ENDPOINT = os.getenv("PRIORITY_AGENT_ENDPOINT", f"http://localhost:{PORT}/submit")

agent = Agent(
    name="priority-agent",
    seed=SEED,
    port=PORT,
    endpoint=[ENDPOINT],
)


SEVERITY_BASE = {
    IssueCategory.POTHOLE: 70,
    IssueCategory.GARBAGE: 50,
    IssueCategory.STREETLIGHT: 60,
    IssueCategory.WATER_LEAKAGE: 80,
    IssueCategory.DRAINAGE: 75,
    IssueCategory.FOOTPATH: 55,
    IssueCategory.OBSTRUCTION: 85,
    IssueCategory.PROPERTY_DAMAGE: 65,
    IssueCategory.SANITATION: 70,
    IssueCategory.OTHER: 40,
}

RISK_BASE = {
    IssueCategory.POTHOLE: 65,
    IssueCategory.GARBAGE: 45,
    IssueCategory.STREETLIGHT: 55,
    IssueCategory.WATER_LEAKAGE: 75,
    IssueCategory.DRAINAGE: 70,
    IssueCategory.FOOTPATH: 50,
    IssueCategory.OBSTRUCTION: 90,
    IssueCategory.PROPERTY_DAMAGE: 55,
    IssueCategory.SANITATION: 60,
    IssueCategory.OTHER: 35,
}


DEFAULT_WEIGHTS = {
    "severity": 0.35,
    "risk": 0.25,
    "time": 0.20,
    "corroboration": 0.20,
}

SAFETY_ESCALATION_THRESHOLD = 85.0


def calculate_time_score(created_at: datetime) -> float:
    hours = (datetime.utcnow() - created_at).total_seconds() / 3600
    if hours < 24:
        return round(hours / 24 * 30, 1)
    elif hours < 168:
        return round(30 + (hours - 24) / 144 * 40, 1)
    else:
        return round(min(100, 70 + (hours - 168) / 168 * 30), 1)


def score_to_band(score: float) -> PriorityBand:
    if score >= 80:
        return PriorityBand.CRITICAL
    elif score >= 60:
        return PriorityBand.HIGH
    elif score >= 35:
        return PriorityBand.MEDIUM
    return PriorityBand.LOW


@agent.on_message(model=PriorityRequest)
async def handle_priority_scoring(ctx: Context, sender: str, msg: PriorityRequest):
    ctx.logger.info(f"Received priority scoring request for report {msg.report_id}")
    
    try:
        category = IssueCategory(msg.category)
        created_at = datetime.fromisoformat(msg.created_at.replace('Z', '+00:00'))
        
        weights = DEFAULT_WEIGHTS
        if msg.rule_version != "v1.0":
            pass
        
        severity = SEVERITY_BASE.get(category, 40)
        if msg.severity_indicators:
            severity = min(100, severity + msg.severity_indicators.get("bonus", 0))
        
        risk = RISK_BASE.get(category, 35)
        if msg.risk_indicators:
            risk = min(100, risk + msg.risk_indicators.get("bonus", 0))
        
        time_score = calculate_time_score(created_at)
        corroboration = min(100, msg.duplicate_count * 15 + 10)
        
        total = round(
            severity * weights["severity"] +
            risk * weights["risk"] +
            time_score * weights["time"] +
            corroboration * weights["corroboration"],
            1
        )
        
        band = score_to_band(total)
        escalation = total >= SAFETY_ESCALATION_THRESHOLD
        escalation_reason = "Priority score exceeds safety escalation threshold" if escalation else None
        
        factor_details = {
            "weights": weights,
            "severity_factors": {"category_base": severity},
            "risk_factors": {"category_base": risk},
            "time_unresolved_hours": round((datetime.utcnow() - created_at).total_seconds() / 3600, 1),
            "duplicate_count": msg.duplicate_count
        }
        
        response = PriorityResponse(
            report_id=msg.report_id,
            priority_score=total,
            priority_band=band.value,
            severity_score=round(severity, 1),
            risk_score=round(risk, 1),
            time_score=time_score,
            corroboration_score=round(corroboration, 1),
            factor_details=factor_details,
            escalation_recommended=escalation,
            escalation_reason=escalation_reason,
            rule_version=msg.rule_version,
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"Sent priority response for report {msg.report_id}: {total} ({band.value})")
        
    except Exception as e:
        ctx.logger.error(f"Priority scoring failed for report {msg.report_id}: {e}")
        error_response = AgentErrorResponse(
            report_id=msg.report_id,
            error_code="PRIORITY_SCORING_FAILED",
            error_message=str(e),
            retryable=True,
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        await ctx.send(sender, error_response)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Priority Agent started. Address: {agent.address}")


if __name__ == "__main__":
    agent.run()