import os
import uuid
from datetime import datetime
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

from agents.common.messages import (
    ClassificationRequest, ClassificationResponse, AgentErrorResponse
)
from agents.common.schemas import IssueCategory


SEED = os.getenv("CLASSIFICATION_AGENT_SEED", "civicpulse-classification-agent-seed")
PORT = int(os.getenv("CLASSIFICATION_AGENT_PORT", "8001"))
ENDPOINT = os.getenv("CLASSIFICATION_AGENT_ENDPOINT", f"http://localhost:{PORT}/submit")

agent = Agent(
    name="classification-agent",
    seed=SEED,
    port=PORT,
    endpoint=[ENDPOINT],
)


class MockVisionAnalyzer:
    CATEGORY_KEYWORDS = {
        IssueCategory.POTHOLE: ["pothole", "hole", "road damage", "crack", "asphalt", "pavement", "road"],
        IssueCategory.GARBAGE: ["garbage", "trash", "waste", "rubbish", "overflow", "bin", "litter", "dump"],
        IssueCategory.STREETLIGHT: ["streetlight", "light", "lamp", "dark", "broken light", "outage", "lighting"],
        IssueCategory.WATER_LEAKAGE: ["water", "leak", "pipe", "burst", "flood", "leaking", "main"],
        IssueCategory.DRAINAGE: ["drain", "blocked", "clogged", "sewer", "flood", "water logging", "storm drain"],
        IssueCategory.FOOTPATH: ["footpath", "sidewalk", "pavement", "cracked", "uneven", "broken", "walkway"],
        IssueCategory.OBSTRUCTION: ["obstruction", "blocked", "debris", "fallen", "tree", "blocking", "hazard"],
        IssueCategory.PROPERTY_DAMAGE: ["damage", "broken", "vandal", "graffiti", "destroyed", "bench", "fixture"],
        IssueCategory.SANITATION: ["sanitation", "toilet", "sewage", "smell", "odor", "hygiene", "restroom"],
    }

    def analyze(self, description: str, category_hint: IssueCategory | None = None) -> tuple:
        desc_lower = description.lower()
        scores = {}
        
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
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
            {"category": cat.value, "confidence": round(min(0.8, confidence - 0.1 * i), 2)}
            for i, cat in enumerate(sorted(scores, key=scores.get, reverse=True)[1:4])
        ]

        evidence_quality = "good" if confidence > 0.7 else "fair" if confidence > 0.5 else "poor"
        needs_review = confidence < 0.7

        return predicted, confidence, alternatives, evidence_quality, needs_review


analyzer = MockVisionAnalyzer()


@agent.on_message(model=ClassificationRequest)
async def handle_classification(ctx: Context, sender: str, msg: ClassificationRequest):
    ctx.logger.info(f"Received classification request for report {msg.report_id}")
    
    try:
        category_hint = None
        if msg.category_hint:
            try:
                category_hint = IssueCategory(msg.category_hint)
            except ValueError:
                pass
        
        predicted, confidence, alternatives, evidence_quality, needs_review = analyzer.analyze(
            msg.description, category_hint
        )
        
        explanation = f"Mock analysis based on text description. Keywords matched for {predicted.value}."
        if msg.image_urls:
            explanation += f" Image analysis simulated for {len(msg.image_urls)} image(s)."
        
        response = ClassificationResponse(
            report_id=msg.report_id,
            predicted_category=predicted.value,
            confidence=confidence,
            alternatives=alternatives,
            explanation=explanation,
            evidence_quality=evidence_quality,
            needs_human_review=needs_review,
            model_version="mock-v1.0",
            is_mock=True,
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"Sent classification response for report {msg.report_id}: {predicted.value} ({confidence:.2f})")
        
    except Exception as e:
        ctx.logger.error(f"Classification failed for report {msg.report_id}: {e}")
        error_response = AgentErrorResponse(
            report_id=msg.report_id,
            error_code="CLASSIFICATION_FAILED",
            error_message=str(e),
            retryable=True,
            correlation_id=msg.correlation_id,
            message_id=str(uuid.uuid4())
        )
        await ctx.send(sender, error_response)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Classification Agent started. Address: {agent.address}")
    if os.getenv("FUND_AGENT", "false").lower() == "true":
        fund_agent_if_low(agent.wallet.address())


if __name__ == "__main__":
    agent.run()