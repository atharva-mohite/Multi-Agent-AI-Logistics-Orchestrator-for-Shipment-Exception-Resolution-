"""Guardrails configuration for the maritime system"""

import logging
from typing import Optional, Dict, Any
from strands.models import BedrockModel
import os

logger = logging.getLogger(__name__)

class GuardrailsConfig:
    """Configure and manage guardrails for agents."""
    
    def __init__(self, enabled: bool = True):
        """Initialize guardrails configuration."""
        self.enabled = enabled
        self.guardrail_id = os.getenv("BEDROCK_GUARDRAIL_ID")
        self.guardrail_version = os.getenv("BEDROCK_GUARDRAIL_VERSION", "1")
        
        logger.info(f"Guardrails initialized (enabled: {self.enabled})")
    
    def create_guarded_model(
        self, 
        model_id: Optional[str] = None,
        **kwargs
    ) -> BedrockModel:
        """
        Create a Bedrock model with guardrails enabled.
        
        Args:
            model_id: Model identifier
            **kwargs: Additional model configuration
            
        Returns:
            Configured BedrockModel with guardrails
        """
        config = {
            "model_id": model_id or os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"),
            "region_name": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        }
        
        # Add guardrails if enabled
        if self.enabled and self.guardrail_id:
            config.update({
                "guardrail_id": self.guardrail_id,
                "guardrail_version": self.guardrail_version,
                "guardrail_trace": "enabled",
                "guardrail_redact_input": True,
                "guardrail_redact_input_message": "[Content blocked by guardrails]",
                "guardrail_redact_output": True,
                "guardrail_redact_output_message": "[Response blocked by guardrails]"
            })
            logger.info(f"Guardrails enabled with ID: {self.guardrail_id}")
        else:
            logger.info("Guardrails not configured or disabled")
        
        # Add any additional kwargs
        config.update(kwargs)
        
        return BedrockModel(**config)
    
    def check_content_policy(self, content: str) -> Dict[str, Any]:
        """
        Check content against policy rules.
        
        Args:
            content: Content to check
            
        Returns:
            Policy check results
        """
        violations = []
        
        # Check for sensitive topics (simplified for demo)
        sensitive_topics = [
            "classified", "confidential", "secret",
            "nuclear", "weapon", "explosive"
        ]
        
        content_lower = content.lower()
        for topic in sensitive_topics:
            if topic in content_lower:
                violations.append({
                    "type": "sensitive_topic",
                    "topic": topic,
                    "severity": "high"
                })
        
        # Check for data patterns that shouldn't be shared
        import re
        
        # Check for coordinates that might be sensitive
        coord_pattern = r'[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)'
        if re.search(coord_pattern, content):
            violations.append({
                "type": "location_data",
                "severity": "medium",
                "note": "Contains precise coordinates"
            })
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "action": "block" if any(v["severity"] == "high" for v in violations) else "warn" if violations else "allow"
        }