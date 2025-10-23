"""News Analyzer Sub-Agent for Maritime Events"""

import random
from datetime import datetime, timedelta
from typing import List, Dict
from strands import Agent
import logging
import json

logger = logging.getLogger(__name__)

class NewsAnalyzerAgent:
    """Analyzes news and events affecting maritime routes."""
    
    def __init__(self):
        """Initialize the news analyzer agent."""
        self.agent = Agent(
            name="news_analyzer",
            system_prompt="""You are a maritime news analyst specializing in identifying 
            events that could impact shipping routes. Analyze news for:
            1. Geopolitical events (conflicts, sanctions, port closures)
            2. Natural disasters (storms, earthquakes, tsunamis)
            3. Maritime incidents (accidents, piracy, congestion)
            4. Economic events (strikes, trade restrictions)
            5. Infrastructure issues (port maintenance, canal closures)
            
            Assess the severity and geographic impact of each event."""
        )
        
        # Predefined news events for simulation
        self.news_templates = [
            {
                "type": "geopolitical",
                "events": [
                    "Increased piracy activity reported",
                    "Naval exercises announced",
                    "New shipping sanctions imposed",
                    "Port security alert issued"
                ]
            },
            {
                "type": "natural",
                "events": [
                    "Tropical storm formation detected",
                    "Severe weather warning issued",
                    "Tsunami watch in effect",
                    "Hurricane tracking update"
                ]
            },
            {
                "type": "maritime",
                "events": [
                    "Container ship collision reported",
                    "Major port congestion developing",
                    "Oil spill cleanup underway",
                    "Search and rescue operation ongoing"
                ]
            },
            {
                "type": "economic",
                "events": [
                    "Port workers strike announced",
                    "New cargo restrictions implemented",
                    "Fuel price surge affecting operations",
                    "Trade route disruption expected"
                ]
            },
            {
                "type": "infrastructure",
                "events": [
                    "Canal maintenance scheduled",
                    "Port expansion causing delays",
                    "Navigation channel dredging",
                    "Terminal equipment failure"
                ]
            }
        ]
    
    def generate_news_for_segment(
        self, 
        segment_id: str,
        segment_coordinates: List[tuple],
        analysis_date: str,
        days_before: int = 7
    ) -> List[Dict]:
        """
        Generate news events for a route segment.
        
        Args:
            segment_id: Identifier for the segment
            segment_coordinates: List of (lat, lon) coordinates
            analysis_date: Date to analyze
            days_before: Days before analysis date to include
            
        Returns:
            List of news events affecting the segment
        """
        news_items = []
        base_date = datetime.strptime(analysis_date, "%Y-%m-%d")
        
        # Generate 2-5 news items per segment
        num_events = random.randint(2, 5)
        
        for _ in range(num_events):
            # Select random event type and template
            event_type = random.choice(self.news_templates)
            event_desc = random.choice(event_type["events"])
            
            # Generate event date within window
            days_ago = random.randint(0, days_before)
            event_date = base_date - timedelta(days=days_ago)
            
            # Calculate affected area
            center_lat = sum(c[0] for c in segment_coordinates) / len(segment_coordinates)
            center_lon = sum(c[1] for c in segment_coordinates) / len(segment_coordinates)
            
            # Determine severity
            severity_levels = ["Low", "Medium", "High", "Critical"]
            weights = [0.4, 0.3, 0.2, 0.1]
            severity = random.choices(severity_levels, weights=weights)[0]
            
            # Calculate impact radius based on severity
            impact_radius = {
                "Low": 50,
                "Medium": 100,
                "High": 200,
                "Critical": 500
            }[severity]
            
            # Duration of impact
            duration_days = random.randint(1, 7) if severity in ["Low", "Medium"] else random.randint(3, 14)
            
            news_item = {
                "id": f"news_{segment_id}_{random.randint(1000, 9999)}",
                "date": event_date.strftime("%Y-%m-%d"),
                "type": event_type["type"],
                "headline": event_desc,
                "severity": severity,
                "location": {
                    "latitude": round(center_lat + random.uniform(-2, 2), 4),
                    "longitude": round(center_lon + random.uniform(-2, 2), 4)
                },
                "affected_radius_nm": impact_radius,
                "duration": {
                    "start_date": event_date.strftime("%Y-%m-%d"),
                    "end_date": (event_date + timedelta(days=duration_days)).strftime("%Y-%m-%d"),
                    "days": duration_days
                },
                "impact": self._generate_impact_assessment(severity, event_type["type"]),
                "recommendations": self._generate_recommendations(severity, event_type["type"])
            }
            
            news_items.append(news_item)
        
        return news_items
    
    def _generate_impact_assessment(self, severity: str, event_type: str) -> Dict:
        """Generate impact assessment for a news event."""
        impact_map = {
            "Low": {"delay_hours": 0.5, "speed_reduction": 0, "risk_increase": 5},
            "Medium": {"delay_hours": 2, "speed_reduction": 2, "risk_increase": 15},
            "High": {"delay_hours": 6, "speed_reduction": 5, "risk_increase": 30},
            "Critical": {"delay_hours": 24, "speed_reduction": 10, "risk_increase": 50}
        }
        
        base_impact = impact_map[severity]
        
        # Adjust based on event type
        if event_type == "natural":
            base_impact["speed_reduction"] *= 1.5
        elif event_type == "geopolitical":
            base_impact["risk_increase"] *= 1.5
        elif event_type == "infrastructure":
            base_impact["delay_hours"] *= 2
        
        return {
            "estimated_delay_hours": base_impact["delay_hours"],
            "speed_reduction_knots": base_impact["speed_reduction"],
            "risk_increase_percent": base_impact["risk_increase"],
            "route_viability": "Viable" if severity in ["Low", "Medium"] else "Compromised"
        }
    
    def _generate_recommendations(self, severity: str, event_type: str) -> List[str]:
        """Generate recommendations based on event severity and type."""
        recommendations = []
        
        if severity in ["High", "Critical"]:
            recommendations.append("Consider alternative routing")
            recommendations.append("Monitor situation closely")
        
        if event_type == "natural":
            recommendations.append("Check weather updates frequently")
            recommendations.append("Ensure vessel is prepared for heavy weather")
        elif event_type == "geopolitical":
            recommendations.append("Verify security protocols")
            recommendations.append("Maintain communication with port authorities")
        elif event_type == "maritime":
            recommendations.append("Increase bridge watch")
            recommendations.append("Reduce speed in congested areas")
        elif event_type == "economic":
            recommendations.append("Confirm port services availability")
            recommendations.append("Prepare for potential delays")
        elif event_type == "infrastructure":
            recommendations.append("Contact port agent for updates")
            recommendations.append("Have contingency plans ready")
        
        return recommendations
    
    def analyze_route_news(
        self,
        route_segments: List[Dict],
        departure_date: str,
        vessel_speed_knots: float
    ) -> Dict:
        """
        Analyze news impact for entire route.
        
        Args:
            route_segments: List of route segments
            departure_date: Departure date
            vessel_speed_knots: Vessel speed
            
        Returns:
            Complete news analysis for the route
        """
        departure = datetime.strptime(departure_date, "%Y-%m-%d")
        cumulative_hours = 0
        all_news = []
        
        for segment in route_segments:
            # Calculate when vessel will be at this segment
            segment_date = departure + timedelta(hours=cumulative_hours)
            
            # Generate news for this segment
            news_items = self.generate_news_for_segment(
                segment_id=segment["segment_id"],
                segment_coordinates=segment["coordinates"],
                analysis_date=segment_date.strftime("%Y-%m-%d")
            )
            
            # Add timing information
            for item in news_items:
                item["vessel_eta"] = segment_date.isoformat()
                item["hours_from_departure"] = cumulative_hours
            
            all_news.extend(news_items)
            
            # Update cumulative time
            segment_distance = segment.get("distance_nm", 100)
            cumulative_hours += segment_distance / vessel_speed_knots
        
        # Analyze overall impact
        critical_events = [n for n in all_news if n["severity"] == "Critical"]
        high_events = [n for n in all_news if n["severity"] == "High"]
        
        overall_risk = "Low"
        if critical_events:
            overall_risk = "Critical"
        elif len(high_events) > 2:
            overall_risk = "High"
        elif high_events:
            overall_risk = "Medium"
        
        return {
            "analysis_date": departure_date,
            "total_events": len(all_news),
            "events_by_severity": {
                "Critical": len(critical_events),
                "High": len(high_events),
                "Medium": len([n for n in all_news if n["severity"] == "Medium"]),
                "Low": len([n for n in all_news if n["severity"] == "Low"])
            },
            "overall_risk_assessment": overall_risk,
            "news_items": all_news,
            "summary": self._generate_news_summary(all_news),
            "recommended_actions": self._generate_route_recommendations(overall_risk, all_news)
        }
    
    def _generate_news_summary(self, news_items: List[Dict]) -> str:
        """Generate a summary of all news events."""
        if not news_items:
            return "No significant events detected along the route."
        
        event_types = {}
        for item in news_items:
            event_type = item["type"]
            if event_type not in event_types:
                event_types[event_type] = 0
            event_types[event_type] += 1
        
        summary_parts = []
        for event_type, count in event_types.items():
            summary_parts.append(f"{count} {event_type} events")
        
        return f"Detected {', '.join(summary_parts)} affecting the route."
    
    def _generate_route_recommendations(self, risk_level: str, news_items: List[Dict]) -> List[str]:
        """Generate overall route recommendations based on news analysis."""
        recommendations = []
        
        if risk_level == "Critical":
            recommendations.append("URGENT: Consider postponing departure or selecting alternative route")
            recommendations.append("Multiple critical events detected along planned route")
        elif risk_level == "High":
            recommendations.append("Review alternative routes for affected segments")
            recommendations.append("Ensure contingency plans are in place")
        elif risk_level == "Medium":
            recommendations.append("Monitor developing situations along the route")
            recommendations.append("Maintain flexibility in scheduling")
        else:
            recommendations.append("Route conditions are generally favorable")
            recommendations.append("Standard precautions recommended")
        
        # Add specific recommendations based on event types
        event_types = set(item["type"] for item in news_items)
        if "natural" in event_types:
            recommendations.append("Monitor weather conditions closely throughout voyage")
        if "geopolitical" in event_types:
            recommendations.append("Verify security protocols and maintain vigilance")
        if "infrastructure" in event_types:
            recommendations.append("Confirm port availability and services before arrival")
        
        return recommendations