"""Profanity Scanner for content moderation"""

import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ProfanityScanner:
    """Scans and filters profanity from text."""
    
    def __init__(self, enabled: bool = True):
        """Initialize profanity scanner."""
        self.enabled = enabled
        
        # Basic profanity word list (simplified for demo)
        # In production, use a comprehensive profanity database
        self.profanity_patterns = [
            r'\b(damn|hell|crap)\b',  # Mild
            r'\b(stupid|idiot|moron)\b',  # Moderate  
            # More severe terms would be added in production
        ]
        
        self.severity_levels = {
            "mild": ["damn", "hell", "crap"],
            "moderate": ["stupid", "idiot", "moron"],
            "severe": []  # Would contain more serious terms
        }
        
        logger.info(f"Profanity Scanner initialized (enabled: {self.enabled})")
    
    def scan(self, text: str) -> Dict:
        """
        Scan text for profanity.
        
        Args:
            text: Text to scan
            
        Returns:
            Scan results with severity and recommendations
        """
        if not self.enabled or not text:
            return {
                "clean": True,
                "severity": "none",
                "found_count": 0,
                "flagged_words": [],
                "recommendation": "Content is clean"
            }
        
        text_lower = text.lower()
        found_words = []
        severity = "none"
        
        # Check each pattern
        for pattern in self.profanity_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            found_words.extend(matches)
        
        # Determine severity
        if found_words:
            for word in found_words:
                if word in self.severity_levels["severe"]:
                    severity = "severe"
                    break
                elif word in self.severity_levels["moderate"] and severity != "severe":
                    severity = "moderate"
                elif word in self.severity_levels["mild"] and severity == "none":
                    severity = "mild"
        
        # Generate recommendation
        recommendation = self._generate_recommendation(severity, len(found_words))
        
        return {
            "clean": len(found_words) == 0,
            "severity": severity,
            "found_count": len(found_words),
            "flagged_words": list(set(found_words)),
            "recommendation": recommendation,
            "cleaned_text": self.clean(text) if found_words else text
        }
    
    def clean(self, text: str) -> str:
        """
        Remove or replace profanity in text.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not self.enabled:
            return text
        
        cleaned = text
        
        for pattern in self.profanity_patterns:
            cleaned = re.sub(pattern, "[****]", cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def _generate_recommendation(self, severity: str, count: int) -> str:
        """Generate recommendation based on severity."""
        if severity == "severe":
            return "Content contains severe profanity. Immediate review required."
        elif severity == "moderate":
            return "Content contains moderate profanity. Consider revision."
        elif severity == "mild":
            return "Content contains mild profanity. Review if customer-facing."
        else:
            return "Content is clean and appropriate."
    
    def scan_dict(self, data: Dict) -> Dict:
        """
        Scan dictionary values for profanity.
        
        Args:
            data: Dictionary to scan
            
        Returns:
            Scan results for all string values
        """
        results = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                results[key] = self.scan(value)
            elif isinstance(value, dict):
                results[key] = self.scan_dict(value)
            elif isinstance(value, list):
                results[key] = [
                    self.scan(item) if isinstance(item, str) else item 
                    for item in value
                ]
        
        return results