"""PII Redaction module for maritime system"""

import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class PIIRedactor:
    """Handles PII detection and redaction."""
    
    def __init__(self, enabled: bool = True):
        """Initialize PII redactor."""
        self.enabled = enabled
        
        # Define PII patterns
        self.patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(?:\+?1?\s?)?(?:\([0-9]{3}\)|[0-9]{3})[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}\b',
            "ssn": r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b',
            "credit_card": r'\b(?:\d{4}[\s-]?){3}\d{4}\b',
            "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            "passport": r'\b[A-Z]{1,2}[0-9]{6,9}\b',
            "name": None  # Will use more sophisticated detection
        }
        
        # Common names for basic detection
        self.common_names = {
            "first_names": ["John", "Jane", "James", "Mary", "Robert", "Patricia", "Michael", "Jennifer"],
            "last_names": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        }
        
        logger.info(f"PII Redactor initialized (enabled: {self.enabled})")
    
    def redact(self, text: str) -> str:
        """
        Redact PII from text.
        
        Args:
            text: Input text to redact
            
        Returns:
            Redacted text
        """
        if not self.enabled or not text:
            return text
        
        redacted = text
        
        # Apply regex patterns
        for pii_type, pattern in self.patterns.items():
            if pattern:
                redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted, flags=re.IGNORECASE)
        
        # Simple name detection
        for name in self.common_names["first_names"] + self.common_names["last_names"]:
            redacted = re.sub(r'\b' + name + r'\b', "[REDACTED_NAME]", redacted, flags=re.IGNORECASE)
        
        return redacted
    
    def redact_dict(self, data: Dict) -> Dict:
        """
        Recursively redact PII from dictionary.
        
        Args:
            data: Dictionary to redact
            
        Returns:
            Redacted dictionary
        """
        if not self.enabled:
            return data
        
        redacted = {}
        for key, value in data.items():
            if isinstance(value, str):
                redacted[key] = self.redact(value)
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = self.redact_list(value)
            else:
                redacted[key] = value
        
        return redacted
    
    def redact_list(self, data: List) -> List:
        """
        Redact PII from list.
        
        Args:
            data: List to redact
            
        Returns:
            Redacted list
        """
        if not self.enabled:
            return data
        
        redacted = []
        for item in data:
            if isinstance(item, str):
                redacted.append(self.redact(item))
            elif isinstance(item, dict):
                redacted.append(self.redact_dict(item))
            elif isinstance(item, list):
                redacted.append(self.redact_list(item))
            else:
                redacted.append(item)
        
        return redacted
    
    def mask_function(self, data: Any, **kwargs) -> Any:
        """
        Masking function for integration with observability platforms.
        
        Args:
            data: Data to mask
            **kwargs: Additional arguments
            
        Returns:
            Masked data
        """
        if isinstance(data, str):
            return self.redact(data)
        elif isinstance(data, dict):
            return self.redact_dict(data)
        elif isinstance(data, list):
            return self.redact_list(data)
        return data