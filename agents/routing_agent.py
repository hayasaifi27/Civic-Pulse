import os
import uuid
from uagents import Agent, Context

from agents.common.messages import RoutingRequest, RoutingResponse, AgentErrorResponse
from agents.common.schemas import IssueCategory, PriorityBand


SEED = os.getenv("ROUTING_AGENT_SEED", "civicpulse-routing-agent-seed")
PORT = int(os.getenv("ROUTING_AGENT_PORT", "8004"))
ENDPOINT = os.getenv("ROUTING_AGENT_ENDPOINT", f"http://localhost:{PORT}/submit")

agent = Agent(
    name="routing-agent",
    seed=SEED,
    port=PORT,
    endpoint=[ENDPOINT],
)


MOCK_DEPARTMENTS = {
    "roads": {"id": "dept-roads", "name": "Roads Department"},
    "sanitation": {"id": "dept-sanitation", "name": "Sanitation Department"},
    "electrical": {"id": "dept-electrical", "name": "Electrical Department"},
    "water_supply": {"id": "dept-water", "name": "Water Supply Department"},
    "drainage": {"id": "dept-drainage", "name": "Drainage Department"},
    "public_works": {"id": "dept-pw", "name": "Public Works"},
}

DEFAULT_ROUTING = {
    IssueCategory.POTHOLE: "roads",
    IssueCategory.GARBAGE: "sanitation",
    IssueCategory.STREETLIGHT: "electrical",
    IssueCategory.WATER_LEAKAGE: "water_supply",
    IssueCategory.DRAINAGE: "drainage",
    IssueCategory.FOOTPATH: "roads",
    IssueCategory.OBSTRUCTION: "roads",
    IssueCategory.PROPERTY_DAMAGE: "public_works",
    IssueCategory.SANITATION: "sanitation",
    IssueCategory.OTHER: "public_works",
}


@agent.on_message(model=RoutingRequest)
async def handle_routing(ctx: Context, sender: str, msg: RoutingRequest):
    ctx.logger.info(f"Received routing request for report {msg.report_id}")
    
    try:
        category = IssueCategory(msg.category)
        priority_band = PriorityBand(msg.priority_band)
        
        dept_code = DEFAULT_ROUTING.get(category, "public_works")
        dept = MOCK_DEPARTMENTS.get(dept_code, MOCK_DEPARTMENTS["public_works"])
        
        needs_review = category == IssueCategory.OTHER or priority_band in [PriorityBand.CRITICAL, PriorityBand.SAFETY_ESCALATION]
        
        response = RoutingResponse(
            report_id=msg.report_id,
            department_id=dept["id"],
            department_name=dept["name"],
            queue="urgent" if priority_band in [PriorityBand.CRITICAL, PriorityBand.SAFETY_ESCALATION] else "standard",
            reason=f"Default routing for category {category.value}" + (f", priority {priority_band.value}" if needs_review else ""),
            needs_manual_review=needs_review,
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"Sent routing response for report {msg.report_id}: {dept['name']}")
        
    except Exception as e:
        ctx.logger.error(f"Routing failed for report {msg.report_id}: {e}")
        error_response = AgentErrorResponse(
            report_id=msg.report_id,
            error_code="ROUTING_FAILED",
            error_message=str(e),
            retryable=True,
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        await ctx.send(sender, error_response)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Routing Agent started. Address: {agent.address}")


if __name__ == "__main__":
    agent.run()