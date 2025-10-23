"""Main orchestrator for Maritime Exception Resolution System using Graph pattern"""
import logging
import os
import json  # Add this
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

from strands import Agent
from strands.multiagent import GraphBuilder
from strands.multiagent.base import Status  # Add this
from strands.telemetry import StrandsTelemetry
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent

# Use absolute imports
from agents.forecast_agent import ForecastAgent
from agents.news_analyzer_agent import NewsAnalyzerAgent
from security.pii_redactor import PIIRedactor
from security.profanity_scanner import ProfanityScanner
from security.guardrails_config import GuardrailsConfig
from config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Enable Strands debug logging if in debug mode
if settings.APP_DEBUG:
    logging.getLogger("strands").setLevel(logging.DEBUG)
    logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)

class SecurityHook(HookProvider):
    """Security hook for PII and profanity scanning."""
    
    def __init__(self, pii_redactor: PIIRedactor, profanity_scanner: ProfanityScanner):
        self.pii_redactor = pii_redactor
        self.profanity_scanner = profanity_scanner
    
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(MessageAddedEvent, self.check_message)
    
    def check_message(self, event: MessageAddedEvent) -> None:
        """Check messages for PII and profanity."""
        if event.message.get("role") == "user":
            content = "".join(
                block.get("text", "") 
                for block in event.message.get("content", [])
            )
            
            if content:
                # Scan for profanity
                profanity_result = self.profanity_scanner.scan(content)
                if not profanity_result["clean"]:
                    logger.warning(
                        f"Profanity detected: {profanity_result['severity']} - "
                        f"{profanity_result['found_count']} instances"
                    )
                
                # Log redacted version for audit
                redacted = self.pii_redactor.redact(content)
                if redacted != content:
                    logger.info("PII detected and redacted in user message")

class MaritimeExceptionResolver:
    """Main orchestrator for the maritime exception resolution system."""
    
    def __init__(self):
        """Initialize the system with all components."""
        logger.info("Initializing Maritime Exception Resolution System...")
        
        # Initialize security components
        self.pii_redactor = PIIRedactor(enabled=settings.ENABLE_PII_REDACTION)
        self.profanity_scanner = ProfanityScanner(enabled=settings.ENABLE_PROFANITY_SCAN)
        self.guardrails = GuardrailsConfig(enabled=settings.ENABLE_GUARDRAILS)
        
        # Create security hook BEFORE using it
        self.security_hook = SecurityHook(self.pii_redactor, self.profanity_scanner)
        
        # Initialize telemetry if enabled
        if settings.ENABLE_TRACING:
            self.telemetry = StrandsTelemetry()
            if settings.OTEL_ENDPOINT:
                self.telemetry.setup_otlp_exporter(endpoint=settings.OTEL_ENDPOINT)
            self.telemetry.setup_console_exporter()
            logger.info("Telemetry initialized")
        
        # Create guarded model
        model = self.guardrails.create_guarded_model()
        
        # Initialize agents (now security_hook exists)
        # Pass the model directly without wrapping in model_config
        self.forecast_agent = ForecastAgent()
        self.forecast_agent.agent.model = model  # Set model on the internal agent
        self.communication_agent = self._create_communication_agent(model)
        self.resolution_agent = self._create_resolution_agent(model)
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info("System initialized successfully")
    
    def _create_communication_agent(self, model) -> Agent:
        """Create the communication agent."""
        return Agent(
            name="communication_agent",
            model=model,
            system_prompt="""You are a maritime communication specialist responsible for:
            1. Presenting route recommendations clearly to users
            2. Gathering user preferences and decisions
            3. Confirming voyage parameters
            4. Providing updates during the journey
            
            Always be professional, clear, and concise in communications.
            Format information for easy understanding by vessel operators.""",
            hooks=[self.security_hook]
        )
    
    def _create_resolution_agent(self, model) -> Agent:
        """Create the resolution agent."""
        return Agent(
            name="resolution_agent", 
            model=model,
            system_prompt="""You are a maritime exception resolution specialist.
            Your role is to:
            1. Monitor voyage progress
            2. Identify deviations from planned routes
            3. Recommend corrective actions
            4. Coordinate with other agents for updates
            5. Ensure safe and efficient voyage completion
            
            Focus on practical, actionable recommendations.""",
            hooks=[self.security_hook]
        )
    
    def _build_graph(self) -> GraphBuilder:
        """Build the agent graph for route analysis."""
        builder = GraphBuilder()
        
        # Add nodes
        builder.add_node(self.forecast_agent.agent, "forecast")
        builder.add_node(self.communication_agent, "communication")
        builder.add_node(self.resolution_agent, "resolution")
        
        # Add edges (dependencies)
        # Forecast -> Communication (present results)
        builder.add_edge("forecast", "communication")
        
        # Communication -> Resolution (after user selection)
        builder.add_edge("communication", "resolution")
        
        # Set entry point
        builder.set_entry_point("forecast")
        
        # Set execution limits
        builder.set_execution_timeout(600)  # 10 minutes
        builder.set_max_node_executions(10)
        
        logger.info("Agent graph built successfully")
        return builder.build()
    
    """Fix for the analyze_route function in main.py"""

    def analyze_route(
        self,
        origin_port: str,
        destination_port: str,
        departure_date: str,
        carrier_id: str,
        user_preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze routes and provide recommendations.
        
        Args:
            origin_port: Origin port name
            destination_port: Destination port name
            departure_date: Departure date (YYYY-MM-DD)
            carrier_id: Carrier identifier
            user_preferences: Optional user preferences
            
        Returns:
            Analysis results and recommendations
        """
        logger.info(f"Starting route analysis: {origin_port} -> {destination_port}")
        
        # Prepare task for the graph
        task_data = {
            "request_type": "route_analysis",
            "parameters": {
                "origin_port": origin_port,
                "destination_port": destination_port,
                "departure_date": departure_date,
                "carrier_id": carrier_id,
                "user_preferences": user_preferences or {}
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Redact PII from task
        task_data = self.pii_redactor.redact_dict(task_data)
        
        # Convert task to string format for the graph
        task = (
            f"Analyze route from {origin_port} to {destination_port}. "
            f"Departure date: {departure_date}, Carrier: {carrier_id}. "
            f"User preferences: {json.dumps(user_preferences or {})}."
        )
        
        try:
            # Execute the graph - pass as string
            task_str = (
                f"Analyze route from {origin_port} to {destination_port}. "
                f"Departure date: {departure_date}, Carrier: {carrier_id}. "
                f"User preferences: {json.dumps(user_preferences or {})}."
            )
            
            result = self.graph(task_str)
            
            # FIXED: Check for Status enum, not string
            from strands.multiagent.base import Status
            
            if result.status == Status.COMPLETED:
                logger.info("Route analysis completed successfully")
                
                # Extract recommendations from results
                recommendations = self._extract_recommendations(result)
                
                return {
                    "status": "success",
                    "recommendations": recommendations,
                    "execution_time": result.execution_time,
                    "nodes_executed": [node.node_id for node in result.execution_order]
                }
            else:
                logger.error(f"Analysis failed with status: {result.status}")
                return {
                    "status": "failed",
                    "error": f"Analysis could not be completed. Status: {result.status}",
                    "details": str(result.failed_nodes) if hasattr(result, 'failed_nodes') else None
                }
                
        except Exception as e:
            logger.error(f"Error during route analysis: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _extract_recommendations(self, graph_result) -> Dict:
        """Extract recommendations from graph execution results."""
        recommendations = {}
        
        # Get forecast agent results
        if "forecast" in graph_result.results:
            forecast_result = graph_result.results["forecast"].result
            recommendations["forecast"] = {
                "analysis": str(forecast_result),
                "timestamp": datetime.now().isoformat()
            }
        
        # Get communication agent results
        if "communication" in graph_result.results:
            comm_result = graph_result.results["communication"].result
            recommendations["communication"] = {
                "message": str(comm_result),
                "formatted": True
            }
        
        # Get resolution agent results
        if "resolution" in graph_result.results:
            resolution_result = graph_result.results["resolution"].result
            recommendations["resolution"] = {
                "actions": str(resolution_result),
                "monitoring": True
            }
        
        return recommendations
    
    def get_route_status(self, route_id: str) -> Dict:
        """
        Get current status of a route.
        
        Args:
            route_id: Route identifier
            
        Returns:
            Current route status
        """
        # This would connect to a real-time monitoring system
        return {
            "route_id": route_id,
            "status": "in_progress",
            "last_update": datetime.now().isoformat(),
            "position": {
                "latitude": 10.5,
                "longitude": -40.2
            },
            "eta": "2024-01-15T14:30:00Z",
            "alerts": []
        }


def main():
    """Main entry point for CLI usage."""
    resolver = MaritimeExceptionResolver()
    
    # Example usage
    result = resolver.analyze_route(
        origin_port="Rotterdam, Netherlands",
        destination_port="New York, USA",
        departure_date="2024-01-10",
        carrier_id="CARRIER_001",
        user_preferences={
            "priority": "safety",
            "avoid_storms": True
        }
    )
    
    print("Analysis Result:")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Recommendations: {result['recommendations']}")
    else:
        print(f"Error: {result.get('error')}")


if __name__ == "__main__":
    main()