"""Communication Agent for user interaction and updates"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from strands import Agent

logger = logging.getLogger(__name__)

class CommunicationAgent:
    """Handles all communication with stakeholders."""
    
    def __init__(self, model=None):
        """Initialize the communication agent."""
        self.agent = Agent(
            name="communication_agent",
            model=model,
            system_prompt="""You are a maritime communication specialist responsible for 
            clear and professional communication with vessel operators and stakeholders.
            
            Your responsibilities include:
            1. Presenting route analysis results in an easy-to-understand format
            2. Highlighting key risks and recommendations
            3. Gathering user preferences and confirmations
            4. Providing status updates during voyages
            5. Alerting about exceptions and changes
            
            Communication guidelines:
            - Be concise but comprehensive
            - Use maritime terminology appropriately
            - Prioritize safety information
            - Format data for quick comprehension
            - Always maintain professional tone
            
            When presenting routes:
            - Lead with the best recommendation
            - Clearly explain trade-offs
            - Highlight critical factors (weather, traffic, news)
            - Provide actionable next steps"""
        )
        logger.info("Communication Agent initialized")
    
    def format_route_recommendations(self, analysis_results: Dict) -> str:
        """
        Format route analysis results for presentation.
        
        Args:
            analysis_results: Raw analysis results from forecast agent
            
        Returns:
            Formatted message for users
        """
        prompt = f"""
        Format the following route analysis results for presentation to a vessel operator:
        
        {analysis_results}
        
        Structure your response as:
        1. Executive Summary (2-3 sentences)
        2. Recommended Route (with key metrics)
        3. Risk Assessment
        4. Alternative Options
        5. Action Items
        
        Use bullet points and clear formatting.
        """
        
        result = self.agent(prompt)
        return self._extract_message(result)
    
    def request_user_confirmation(self, route_details: Dict) -> str:
        """
        Generate confirmation request for selected route.
        
        Args:
            route_details: Details of selected route
            
        Returns:
            Confirmation message
        """
        prompt = f"""
        Generate a confirmation request for the following selected route:
        
        Route Details: {route_details}
        
        Include:
        - Summary of selected route
        - Key conditions and risks
        - Request for confirmation
        - Next steps after confirmation
        """
        
        result = self.agent(prompt)
        return self._extract_message(result)
    
    def generate_departure_notification(
        self,
        route_id: str,
        departure_date: str,
        vessel_details: Dict
    ) -> str:
        """
        Generate departure notification message.
        
        Args:
            route_id: Selected route ID
            departure_date: Actual departure date
            vessel_details: Vessel information
            
        Returns:
            Departure notification
        """
        prompt = f"""
        Generate a departure notification for:
        - Route: {route_id}
        - Departure: {departure_date}
        - Vessel: {vessel_details}
        
        Include:
        - Confirmation of departure
        - Initial voyage parameters
        - Communication schedule
        - Emergency contacts
        """
        
        result = self.agent(prompt)
        return self._extract_message(result)
    
    def generate_status_update(
        self,
        current_position: Dict,
        progress: Dict,
        conditions: Dict,
        alerts: List[str]
    ) -> str:
        """
        Generate voyage status update.
        
        Args:
            current_position: Current vessel position
            progress: Progress metrics
            conditions: Current conditions
            alerts: Active alerts
            
        Returns:
            Status update message
        """
        prompt = f"""
        Generate a voyage status update:
        
        Position: {current_position}
        Progress: {progress}
        Conditions: {conditions}
        Alerts: {alerts}
        
        Format as a brief but informative update including:
        - Current position and progress
        - Weather and traffic conditions
        - Any deviations or concerns
        - ETA update if changed
        """
        
        result = self.agent(prompt)
        return self._extract_message(result)
    
    def generate_exception_alert(
        self,
        exception_type: str,
        severity: str,
        details: Dict,
        recommendations: List[str]
    ) -> str:
        """
        Generate exception alert message.
        
        Args:
            exception_type: Type of exception
            severity: Severity level
            details: Exception details
            recommendations: Recommended actions
            
        Returns:
            Alert message
        """
        prompt = f"""
        Generate an exception alert for maritime operations:
        
        Exception Type: {exception_type}
        Severity: {severity}
        Details: {details}
        
        Recommended Actions:
        {recommendations}
        
        Structure the alert with:
        - Clear severity indicator
        - Concise problem description
        - Impact assessment
        - Immediate actions required
        - Follow-up recommendations
        """
        
        result = self.agent(prompt)
        return self._extract_message(result)
    
    def generate_arrival_notification(
        self,
        port: str,
        arrival_time: str,
        voyage_summary: Dict
    ) -> str:
        """
        Generate arrival notification.
        
        Args:
            port: Arrival port
            arrival_time: Arrival time
            voyage_summary: Voyage statistics
            
        Returns:
            Arrival notification
        """
        prompt = f"""
        Generate an arrival notification for:
        
        Port: {port}
        Arrival Time: {arrival_time}
        Voyage Summary: {voyage_summary}
        
        Include:
        - Confirmation of safe arrival
        - Voyage statistics
        - Any notable events
        - Next steps for port operations
        """
        
        result = self.agent(prompt)
        return self._extract_message(result)
    
    def format_weather_advisory(self, weather_data: Dict) -> str:
        """
        Format weather advisory for operators.
        
        Args:
            weather_data: Weather forecast data
            
        Returns:
            Formatted weather advisory
        """
        prompt = f"""
        Format the following weather data as a maritime weather advisory:
        
        {weather_data}
        
        Include:
        - Current conditions
        - Forecast for next 24-48 hours
        - Any warnings or watches
        - Recommended precautions
        """
        
        result = self.agent(prompt)
        return self._extract_message(result)
    
    def _extract_message(self, agent_result) -> str:
        """Extract message text from agent result."""
        if isinstance(agent_result, dict):
            if "message" in agent_result:
                message = agent_result["message"]
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                    if isinstance(content, list) and content:
                        return content[0].get("text", str(agent_result))
            return str(agent_result)
        return str(agent_result)