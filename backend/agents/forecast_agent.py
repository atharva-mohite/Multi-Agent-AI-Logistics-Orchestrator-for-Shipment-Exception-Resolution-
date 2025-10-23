"""Forecast Agent for route recommendation"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from strands import Agent
from strands.models import BedrockModel

# Use absolute imports
from tools.weather_forecast import get_weather_forecast, get_extended_forecast
from tools.maritime_traffic import analyze_maritime_traffic, get_traffic_forecast
from tools.route_calculator import (
    find_routes_between_ports,
    calculate_route_time,
    get_carrier_info
)
from agents.news_analyzer_agent import NewsAnalyzerAgent
import json

logger = logging.getLogger(__name__)

class ForecastAgent:
    """Main agent for analyzing and recommending maritime routes."""
    
    def __init__(self, model_config: Optional[Dict] = None):
        """Initialize the forecast agent with tools and sub-agents."""
        
        # Configure model
        if model_config and 'model' in model_config:
        # If a model object is passed, use it directly
            self.model = model_config['model']
        elif model_config:
            self.model = BedrockModel(**model_config)
        else:
            self.model = BedrockModel(
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                temperature=0.3
            )
        
        # Initialize main agent with tools
        self.agent = Agent(
            name="forecast_agent",
            model=self.model,
            tools=[
                get_weather_forecast,
                get_extended_forecast,
                analyze_maritime_traffic,
                get_traffic_forecast,
                find_routes_between_ports,
                calculate_route_time,
                get_carrier_info
            ],
            system_prompt="""You are a maritime route planning expert specializing in 
            exception resolution and route optimization. Your role is to:
            
            1. Analyze multiple route alternatives between ports
            2. Evaluate weather conditions, maritime traffic, and news events
            3. Calculate distances, travel times, and risk factors
            4. Recommend the best route with detailed justification
            5. Provide alternative routes with comparative analysis
            
            Consider these factors in your analysis:
            - Weather conditions and forecasts for each segment
            - Maritime traffic density and congestion
            - News events and their impact on route viability
            - Total distance and estimated travel time
            - Carrier capabilities and average speeds
            - Risk levels and safety considerations
            
            Provide clear, actionable recommendations with supporting data."""
        )
        
        # Initialize sub-agents
        self.news_analyzer = NewsAnalyzerAgent()
        
        logger.info("Forecast Agent initialized successfully")
    
    def analyze_routes(
        self,
        origin_port: str,
        destination_port: str,
        departure_date: str,
        carrier_id: str,
        preferred_arrival_date: Optional[str] = None
    ) -> Dict:
        """
        Analyze all available routes between ports and provide recommendations.
        
        Args:
            origin_port: Name of origin port
            destination_port: Name of destination port  
            departure_date: Departure date (YYYY-MM-DD)
            carrier_id: Carrier identifier
            preferred_arrival_date: Preferred arrival date (optional)
            
        Returns:
            Complete route analysis with recommendations
        """
        logger.info(f"Analyzing routes from {origin_port} to {destination_port}")
        
        try:
            # Get carrier information
            carrier_info = get_carrier_info(carrier_id)
            if not carrier_info:
                return {
                    "error": f"Carrier {carrier_id} not found",
                    "status": "failed"
                }
            
            vessel_speed = carrier_info["avg_speed_knots"]
            
            # Find all available routes
            routes = find_routes_between_ports(origin_port, destination_port)
            if not routes:
                return {
                    "error": f"No routes found between {origin_port} and {destination_port}",
                    "status": "failed"
                }
            
            logger.info(f"Found {len(routes)} routes to analyze")
            
            # Analyze each route
            route_analyses = []
            for route in routes:
                analysis = self._analyze_single_route(
                    route=route,
                    departure_date=departure_date,
                    vessel_speed=vessel_speed,
                    carrier_info=carrier_info
                )
                route_analyses.append(analysis)
            
            # Score and rank routes
            scored_routes = self._score_routes(route_analyses)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                scored_routes=scored_routes,
                origin=origin_port,
                destination=destination_port,
                departure_date=departure_date,
                carrier_info=carrier_info,
                preferred_arrival=preferred_arrival_date
            )
            
            return {
                "status": "success",
                "analysis_timestamp": datetime.now().isoformat(),
                "route_summary": {
                    "origin": origin_port,
                    "destination": destination_port,
                    "departure_date": departure_date,
                    "carrier": carrier_info,
                    "routes_analyzed": len(routes)
                },
                "detailed_analyses": route_analyses,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing routes: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _analyze_single_route(
        self,
        route: Dict,
        departure_date: str,
        vessel_speed: float,
        carrier_info: Dict
    ) -> Dict:
        """Analyze a single route for all factors."""
        
        logger.debug(f"Analyzing route {route['route_id']}")
        
        # Get weather forecast for route segments
        weather_forecast = get_extended_forecast(
            route_segments=route["segments"],
            departure_date=departure_date,
            vessel_speed_knots=vessel_speed
        )
        
        # Get traffic forecast
        traffic_forecast = get_traffic_forecast(
            route_segments=route["segments"],
            departure_date=departure_date,
            vessel_speed_knots=vessel_speed
        )
        
        # Get news analysis
        news_analysis = self.news_analyzer.analyze_route_news(
            route_segments=route["segments"],
            departure_date=departure_date,
            vessel_speed_knots=vessel_speed
        )
        
        # Calculate overall metrics
        total_weather_risk = sum(
            1 for f in weather_forecast 
            if f["segment_summary"]["risk_level"] in ["Medium", "High"]
        )
        
        total_traffic_congestion = sum(
            1 for t in traffic_forecast
            if t["traffic_summary"]["congestion_level"] in ["Medium", "High"]
        )
        
        # Calculate time with impacts
        time_calculation = calculate_route_time(
            route=route,
            vessel_speed_knots=vessel_speed,
            weather_impact={"average_wind_speed": 15} if total_weather_risk > 1 else None,
            traffic_impact={"congestion_level": "High"} if total_traffic_congestion > 1 else None
        )
        
        return {
            "route_id": route["route_id"],
            "route_type": route["route_type"],
            "distance_nm": route["total_distance_nm"],
            "segments": len(route["segments"]),
            "time_calculation": time_calculation,
            "weather_analysis": {
                "risk_segments": total_weather_risk,
                "overall_risk": "High" if total_weather_risk > 2 else "Medium" if total_weather_risk > 0 else "Low",
                "critical_conditions": [
                    f["segment_summary"]["predominant_condition"] 
                    for f in weather_forecast 
                    if f["segment_summary"]["risk_level"] == "High"
                ],
                "forecast_summary": weather_forecast
            },
            "traffic_analysis": {
                "congested_segments": total_traffic_congestion,
                "overall_congestion": "High" if total_traffic_congestion > 2 else "Medium" if total_traffic_congestion > 0 else "Low",
                "peak_traffic_areas": [
                    t["segment_id"] 
                    for t in traffic_forecast 
                    if t["traffic_summary"]["congestion_level"] == "High"
                ],
                "traffic_summary": traffic_forecast
            },
            "news_analysis": news_analysis
        }
    
    def _score_routes(self, route_analyses: List[Dict]) -> List[Dict]:
        """Score and rank routes based on multiple factors."""
        
        for analysis in route_analyses:
            score = 100  # Start with perfect score
            
            # Distance penalty (shorter is better)
            base_distance = min(a["distance_nm"] for a in route_analyses)
            distance_penalty = (analysis["distance_nm"] - base_distance) / base_distance * 10
            score -= distance_penalty
            
            # Time penalty
            base_time = min(a["time_calculation"]["total_time_hours"] for a in route_analyses)
            time_penalty = (analysis["time_calculation"]["total_time_hours"] - base_time) / base_time * 15
            score -= time_penalty
            
            # Weather risk penalty
            if analysis["weather_analysis"]["overall_risk"] == "High":
                score -= 20
            elif analysis["weather_analysis"]["overall_risk"] == "Medium":
                score -= 10
            
            # Traffic congestion penalty
            if analysis["traffic_analysis"]["overall_congestion"] == "High":
                score -= 15
            elif analysis["traffic_analysis"]["overall_congestion"] == "Medium":
                score -= 7
            
            # News event penalty
            if analysis["news_analysis"]["overall_risk_assessment"] == "Critical":
                score -= 30
            elif analysis["news_analysis"]["overall_risk_assessment"] == "High":
                score -= 20
            elif analysis["news_analysis"]["overall_risk_assessment"] == "Medium":
                score -= 10
            
            analysis["route_score"] = max(0, score)
        
        # Sort by score
        route_analyses.sort(key=lambda x: x["route_score"], reverse=True)
        
        return route_analyses
    
    def _generate_recommendations(
        self,
        scored_routes: List[Dict],
        origin: str,
        destination: str,
        departure_date: str,
        carrier_info: Dict,
        preferred_arrival: Optional[str]
    ) -> Dict:
        """Generate detailed recommendations based on analysis."""
        
        if not scored_routes:
            return {"error": "No routes to recommend"}
        
        best_route = scored_routes[0]
        alternative_routes = scored_routes[1:3] if len(scored_routes) > 1 else []
        
        recommendations = {
            "best_route": {
                "route_id": best_route["route_id"],
                "score": best_route["route_score"],
                "distance_nm": best_route["distance_nm"],
                "estimated_time": best_route["time_calculation"],
                "key_advantages": self._get_route_advantages(best_route),
                "potential_risks": self._get_route_risks(best_route),
                "detailed_explanation": self._generate_route_explanation(best_route, is_best=True)
            },
            "alternative_routes": []
        }
        
        for i, alt_route in enumerate(alternative_routes, 1):
            recommendations["alternative_routes"].append({
                "rank": i + 1,
                "route_id": alt_route["route_id"],
                "score": alt_route["route_score"],
                "distance_nm": alt_route["distance_nm"],
                "estimated_time": alt_route["time_calculation"],
                "comparison_to_best": self._compare_routes(best_route, alt_route),
                "when_to_consider": self._when_to_consider_alternative(alt_route),
                "detailed_explanation": self._generate_route_explanation(alt_route, is_best=False)
            })
        
        # Overall recommendation
        recommendations["executive_summary"] = self._generate_executive_summary(
            best_route, alternative_routes, carrier_info
        )
        
        recommendations["action_items"] = self._generate_action_items(best_route)
        
        return recommendations
    
    def _get_route_advantages(self, route: Dict) -> List[str]:
        """Identify key advantages of a route."""
        advantages = []
        
        if route["weather_analysis"]["overall_risk"] == "Low":
            advantages.append("Favorable weather conditions throughout journey")
        if route["traffic_analysis"]["overall_congestion"] == "Low":
            advantages.append("Low maritime traffic density")
        if route["news_analysis"]["overall_risk_assessment"] == "Low":
            advantages.append("No significant security or operational concerns")
        if route.get("route_score", 0) > 80:
            advantages.append("Optimal balance of distance and conditions")
        
        return advantages
    
    def _get_route_risks(self, route: Dict) -> List[str]:
        """Identify potential risks of a route."""
        risks = []
        
        if route["weather_analysis"]["overall_risk"] in ["Medium", "High"]:
            risks.append(f"{route['weather_analysis']['overall_risk']} weather risk in {route['weather_analysis']['risk_segments']} segments")
        if route["traffic_analysis"]["overall_congestion"] in ["Medium", "High"]:
            risks.append(f"{route['traffic_analysis']['overall_congestion']} traffic congestion expected")
        if route["news_analysis"]["overall_risk_assessment"] in ["Medium", "High", "Critical"]:
            risks.append(f"{route['news_analysis']['total_events']} news events may impact journey")
        
        return risks
    
    def _generate_route_explanation(self, route: Dict, is_best: bool) -> str:
        """Generate detailed explanation for a route."""
        explanation_parts = []
        
        if is_best:
            explanation_parts.append(
                f"This route scores {route['route_score']:.1f}/100 and offers the best overall conditions."
            )
        else:
            explanation_parts.append(
                f"This alternative route scores {route['route_score']:.1f}/100."
            )
        
        explanation_parts.append(
            f"Total distance: {route['distance_nm']:.1f} nautical miles, "
            f"estimated time: {route['time_calculation']['total_time_days']:.1f} days."
        )
        
        # Weather assessment
        weather = route["weather_analysis"]
        explanation_parts.append(
            f"Weather conditions are {weather['overall_risk'].lower()} risk with "
            f"{weather['risk_segments']} segments potentially affected."
        )
        
        # Traffic assessment
        traffic = route["traffic_analysis"]
        explanation_parts.append(
            f"Maritime traffic shows {traffic['overall_congestion'].lower()} congestion levels."
        )
        
        # News assessment
        news = route["news_analysis"]
        if news["total_events"] > 0:
            explanation_parts.append(
                f"News analysis identifies {news['total_events']} events with "
                f"{news['overall_risk_assessment'].lower()} overall impact."
            )
        
        return " ".join(explanation_parts)
    
    def _compare_routes(self, best: Dict, alternative: Dict) -> Dict:
        """Compare alternative route to best route."""
        return {
            "distance_difference_nm": alternative["distance_nm"] - best["distance_nm"],
            "time_difference_hours": (
                alternative["time_calculation"]["total_time_hours"] - 
                best["time_calculation"]["total_time_hours"]
            ),
            "score_difference": alternative["route_score"] - best["route_score"],
            "risk_comparison": {
                "weather": f"{alternative['weather_analysis']['overall_risk']} vs {best['weather_analysis']['overall_risk']}",
                "traffic": f"{alternative['traffic_analysis']['overall_congestion']} vs {best['traffic_analysis']['overall_congestion']}",
                "news": f"{alternative['news_analysis']['overall_risk_assessment']} vs {best['news_analysis']['overall_risk_assessment']}"
            }
        }
    
    def _when_to_consider_alternative(self, route: Dict) -> str:
        """Determine when an alternative route should be considered."""
        conditions = []
        
        if route["weather_analysis"]["overall_risk"] == "Low":
            conditions.append("weather sensitivity is high")
        if route["traffic_analysis"]["overall_congestion"] == "Low":
            conditions.append("schedule flexibility is limited")
        if route["distance_nm"] < 1000:
            conditions.append("fuel efficiency is priority")
        
        if conditions:
            return f"Consider this route when {' or '.join(conditions)}"
        return "Consider as backup option"
    
    def _generate_executive_summary(
        self, 
        best_route: Dict,
        alternatives: List[Dict],
        carrier_info: Dict
    ) -> str:
        """Generate executive summary of recommendations."""
        summary = (
            f"Route analysis complete for {carrier_info['carrier_name']} "
            f"(vessel speed: {carrier_info['avg_speed_knots']} knots). "
            f"Recommended route {best_route['route_id']} scores {best_route['route_score']:.1f}/100 "
            f"with estimated transit time of {best_route['time_calculation']['total_time_days']:.1f} days. "
        )
        
        if best_route["weather_analysis"]["overall_risk"] == "Low" and \
           best_route["traffic_analysis"]["overall_congestion"] == "Low":
            summary += "Conditions are favorable with minimal risks identified. "
        else:
            summary += "Some operational challenges expected but manageable with proper planning. "
        
        if alternatives:
            summary += f"{len(alternatives)} alternative routes available if conditions change."
        
        return summary
    
    def _generate_action_items(self, route: Dict) -> List[str]:
        """Generate action items based on selected route."""
        actions = [
            "Confirm vessel readiness for departure",
            "Brief crew on selected route and conditions",
            "Establish communication schedule with shore support"
        ]
        
        if route["weather_analysis"]["overall_risk"] in ["Medium", "High"]:
            actions.append("Monitor weather updates every 6 hours")
            actions.append("Ensure heavy weather preparations complete")
        
        if route["traffic_analysis"]["overall_congestion"] in ["Medium", "High"]:
            actions.append("Plan for reduced speed in congested areas")
            actions.append("Maintain enhanced bridge watch")
        
        if route["news_analysis"]["total_events"] > 5:
            actions.append("Review security protocols")
            actions.append("Monitor news updates for affected areas")
        
        return actions