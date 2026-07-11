"""Agent Orchestrator - Coordinates multi-agent workflow."""
from typing import Dict, Any, Optional
from datetime import datetime
import time
import json

from agents.ingestion.agent import IngestionAgent
from agents.classifier.agent import ClassifierAgent
from agents.billing.agent import BillingAgent
from agents.technical.agent import TechnicalAgent
from agents.retention.agent import RetentionAgent
from agents.escalation.agent import EscalationAgent
from agents.formatter.agent import FormatterAgent
from agents.base_agent import AgentResponse
from models import CustomerTicket, TicketStatus, TicketPriority, get_db, init_db
from utils import logger, calculate_sentiment
from config import ESCALATION_CONFIDENCE_THRESHOLD

class AgentOrchestrator:
    """Orchestrates the multi-agent workflow for customer support."""

    def __init__(self):
        self.ingestion_agent = IngestionAgent()
        self.classifier_agent = ClassifierAgent()
        self.billing_agent = BillingAgent()
        self.technical_agent = TechnicalAgent()
        self.retention_agent = RetentionAgent()
        self.escalation_agent = EscalationAgent()
        self.formatter_agent = FormatterAgent()

        self.agent_map = {
            "billing": self.billing_agent,
            "technical": self.technical_agent,
            "retention": self.retention_agent,
            "sales": self.billing_agent,  # Sales queries handled by billing for now
            "general": self.billing_agent,  # General queries default to billing
        }

        # Initialize database
        init_db()
        logger.info("AgentOrchestrator initialized")

    def process_message(self, message: str, customer_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a customer message through the multi-agent pipeline.

        Pipeline:
        1. Ingestion → 2. Classification → 3. Specialized Agent → 4. Formatter
        (Escalation branch if needed)
        """
        if customer_context is None:
            customer_context = {}

        overall_start = time.time()
        pipeline_log = []

        try:
            # Step 1: Ingestion
            logger.info("Step 1: Ingestion")
            ingestion_result = self.ingestion_agent.process(message, customer_context)
            context = ingestion_result.metadata
            pipeline_log.append({
                "step": "ingestion",
                "agent": ingestion_result.agent_name,
                "confidence": ingestion_result.confidence
            })

            # Step 2: Classification
            logger.info("Step 2: Classification")
            classification_result = self.classifier_agent.process(message, context)
            intent = classification_result.intent
            confidence = classification_result.confidence
            context = classification_result.metadata
            pipeline_log.append({
                "step": "classification",
                "agent": classification_result.agent_name,
                "intent": intent,
                "confidence": confidence,
                "requires_escalation": classification_result.requires_escalation
            })

            # Step 3: Route to specialized agent or escalation
            if classification_result.requires_escalation:
                logger.info("Step 3: Escalation")
                context["escalation_reason"] = classification_result.escalation_reason
                context["previous_agent"] = "Classifier"
                result = self.escalation_agent.process(message, context)
                status = TicketStatus.ESCALATED
                priority = TicketPriority.HIGH
            else:
                # Route to appropriate agent
                agent = self.agent_map.get(intent, self.billing_agent)
                logger.info(f"Step 3: Specialized Agent ({agent.name})")

                result = agent.process(message, context)

                # Check if agent escalated
                if result.requires_escalation:
                    logger.info("Step 3b: Agent Escalation")
                    context["escalation_reason"] = result.escalation_reason
                    context["previous_agent"] = agent.name
                    result = self.escalation_agent.process(message, context)
                    status = TicketStatus.ESCALATED
                    priority = TicketPriority.HIGH
                else:
                    status = TicketStatus.RESOLVED
                    priority = self._determine_priority(context)

                pipeline_log.append({
                    "step": "specialized_agent",
                    "agent": result.agent_name,
                    "confidence": result.confidence
                })

            # Step 4: Format response
            logger.info("Step 4: Formatting")
            context["agent_response"] = result.response
            context["status"] = status.value
            formatted = self.formatter_agent.process(message, context)

            pipeline_log.append({
                "step": "formatting",
                "agent": formatted.agent_name
            })

            # Save to database
            self._save_ticket(message, context, result, status, priority)

            total_time = time.time() - overall_start

            return {
                "success": True,
                "ticket_id": context.get("ticket_id"),
                "customer_id": context.get("customer_id"),
                "intent": intent,
                "confidence": confidence,
                "sentiment": context.get("sentiment", 0.0),
                "status": status.value,
                "priority": priority.value,
                "response": formatted.response,
                "requires_escalation": result.requires_escalation,
                "escalation_reason": result.escalation_reason if result.requires_escalation else None,
                "processing_time": round(total_time, 2),
                "pipeline": pipeline_log,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your request. Please try again or call 121 for immediate assistance.",
                "timestamp": datetime.utcnow().isoformat()
            }

    def _determine_priority(self, context: Dict[str, Any]) -> TicketPriority:
        """Determine ticket priority based on context."""
        sentiment = context.get("sentiment", 0.0)

        if sentiment < -0.5:
            return TicketPriority.HIGH
        elif sentiment < -0.2:
            return TicketPriority.MEDIUM
        return TicketPriority.LOW

    def _save_ticket(self, message: str, context: Dict[str, Any], 
                     result: AgentResponse, status: TicketStatus, priority: TicketPriority):
        """Save ticket to database."""
        try:
            db = next(get_db())
            ticket = CustomerTicket(
                ticket_id=context.get("ticket_id", "UNKNOWN"),
                customer_id=context.get("customer_id", ""),
                customer_name=context.get("customer_name", ""),
                customer_phone=context.get("customer_phone", ""),
                message=message,
                intent=result.intent,
                confidence=result.confidence,
                sentiment=context.get("sentiment", 0.0),
                assigned_agent=result.agent_name,
                status=status,
                priority=priority,
                response=result.response,
                metadata_json={
                    "pipeline": context.get("pipeline", []),
                    "escalation_reason": result.escalation_reason if result.requires_escalation else None
                }
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            logger.info(f"Saved ticket {ticket.ticket_id} to database")
        except Exception as e:
            logger.error(f"Failed to save ticket: {e}")

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        stats = {
            "agents": {
                "billing": self.billing_agent.get_metrics(),
                "technical": self.technical_agent.get_metrics(),
                "retention": self.retention_agent.get_metrics(),
                "escalation": self.escalation_agent.get_metrics()
            },
            "escalation_queue": len(self.escalation_agent.get_queue()),
            "timestamp": datetime.utcnow().isoformat()
        }
        return stats

# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None

def get_orchestrator() -> AgentOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
