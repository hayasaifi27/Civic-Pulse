import os
import uuid
from datetime import datetime
from uagents import Agent, Context

from agents.common.messages import MonitoringRequest, MonitoringResponse, AgentErrorResponse
from agents.common.schemas import PriorityBand


SEED = os.getenv("MONITORING_AGENT_SEED", "civicpulse-monitoring-agent-seed")
PORT = int(os.getenv("MONITORING_AGENT_PORT", "8005"))
ENDPOINT = os.getenv("MONITORING_AGENT_ENDPOINT", f"http://localhost:{PORT}/submit")

agent = Agent(
    name="monitoring-agent",
    seed=SEED,
    port=PORT,
    endpoint=[ENDPOINT],
)


SLA_HOURS = {
    "low": 168,
    "medium": 72,
    "high": 48,
    "critical": 24,
    "safety_escalation": 12,
}


@agent.on_message(model=MonitoringRequest)
async def handle_monitoring(ctx: Context, sender: str, msg: MonitoringRequest):
    ctx.logger.info(f"Received monitoring request for report {msg.report_id}")
    
    try:
        priority_band = PriorityBand(msg.priority_band)
        sla_hours = SLA_HOURS.get(priority_band.value, 72)
        
        last_update = datetime.fromisoformat(msg.last_update.replace('Z', '+00:00'))
        hours_since_update = (datetime.utcnow() - last_update).total_seconds() / 3600
        
        overdue = hours_since_update > sla_hours
        
        escalation_recommended = False
        escalation_reason = None
        notification_event = None
        
        if overdue:
            escalation_recommended = True
            escalation_reason = f"Report overdue by {hours_since_update - sla_hours:.1f} hours (SLA: {sla_hours}h)"
            notification_event = "overdue_escalation"
        elif hours_since_update > sla_hours * 0.8:
            notification_event = "sla_warning"
        
        if msg.sla_deadline:
            deadline = datetime.fromisoformat(msg.sla_deadline.replace('Z', '+00:00'))
            if datetime.utcnow() > deadline:
                overdue = True
                escalation_recommended = True
                escalation_reason = "SLA deadline passed"
                notification_event = "sla_breach"
        
        response = MonitoringResponse(
            report_id=msg.report_id,
            overdue=overdue,
            escalation_recommended=escalation_recommended,
            escalation_reason=escalation_reason,
            notification_event=notification_event,
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"Sent monitoring response for report {msg.report_id}: overdue={overdue}")
        
    except Exception as e:
        ctx.logger.error(f"Monitoring failed for report {msg.report_id}: {e}")
        error_response = AgentErrorResponse(
            report_id=msg.report_id,
            error_code="MONITORING_FAILED",
            error_message=str(e),
            retryable=True,
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        await ctx.send(sender, error_response)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Monitoring Agent started. Address: {agent.address}")


if __name__ == "__main__":
    agent.run()