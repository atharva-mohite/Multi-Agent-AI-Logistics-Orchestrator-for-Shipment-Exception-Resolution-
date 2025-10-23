"""Maritime Traffic Analysis Tool"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from strands import tool
import logging

logger = logging.getLogger(__name__)

@tool
def analyze_maritime_traffic(
    segment_id: str,
    coordinates: List[Tuple[float, float]],
    analysis_date: str,
    time_window_hours: int = 24
) -> Dict:
    """
    Analyze maritime traffic for a route segment.
    
    Args:
        segment_id: Identifier for the route segment
        coordinates: List of (lat, lon) tuples defining the segment
        analysis_date: Date to analyze traffic (YYYY-MM-DD)
        time_window_hours: Hours to analyze around the date
        
    Returns:
        Maritime traffic analysis for the segment
    """
    
    logger.debug(f"Analyzing maritime traffic for segment {segment_id} on {analysis_date}")
    
    # Simulate traffic patterns based on location
    lat_avg = sum(c[0] for c in coordinates) / len(coordinates)
    lon_avg = sum(c[1] for c in coordinates) / len(coordinates)
    
    # Major shipping lanes have more traffic
    is_major_lane = (
        (-10 < lat_avg < 10) or  # Equatorial routes
        (30 < lat_avg < 40) or   # Mediterranean/Atlantic routes
        (-35 < lat_avg < -25)    # Cape routes
    )
    
    base_traffic = 50 if is_major_lane else 20
    
    # Generate traffic data
    vessel_types = {
        "Container": 0.4,
        "Tanker": 0.25,
        "Bulk Carrier": 0.2,
        "General Cargo": 0.1,
        "Other": 0.05
    }
    
    # Calculate vessel counts
    total_vessels = base_traffic + random.randint(-10, 20)
    vessels_by_type = {}
    for v_type, proportion in vessel_types.items():
        vessels_by_type[v_type] = int(total_vessels * proportion)
    
    # Generate congestion metrics
    congestion_level = "Low"
    if total_vessels > 60:
        congestion_level = "High"
    elif total_vessels > 40:
        congestion_level = "Medium"
    
    # Port proximity affects traffic
    port_proximity_factor = random.uniform(0.8, 1.5)
    
    # Calculate metrics
    traffic_density = total_vessels / (len(coordinates) * 10)  # vessels per 10nm
    average_speed_reduction = 0
    
    if congestion_level == "High":
        average_speed_reduction = random.uniform(2, 5)
    elif congestion_level == "Medium":
        average_speed_reduction = random.uniform(0.5, 2)
    
    # Generate hourly distribution
    hourly_traffic = []
    for hour in range(24):
        # Traffic peaks during business hours
        if 6 <= hour <= 18:
            multiplier = 1.2
        elif 22 <= hour or hour <= 4:
            multiplier = 0.7
        else:
            multiplier = 1.0
        
        hourly_count = int(total_vessels / 24 * multiplier * random.uniform(0.8, 1.2))
        hourly_traffic.append({
            "hour": hour,
            "vessel_count": hourly_count,
            "congestion": "High" if hourly_count > total_vessels/20 else "Normal"
        })
    
    # Collision risk assessment
    collision_risk = "Low"
    if traffic_density > 5 and congestion_level == "High":
        collision_risk = "Medium"
    if traffic_density > 8:
        collision_risk = "High"
    
    return {
        "segment_id": segment_id,
        "analysis_date": analysis_date,
        "coordinates_analyzed": len(coordinates),
        "traffic_summary": {
            "total_vessels_24h": total_vessels,
            "vessels_by_type": vessels_by_type,
            "congestion_level": congestion_level,
            "traffic_density": round(traffic_density, 2),
            "average_speed_reduction_knots": round(average_speed_reduction, 1)
        },
        "hourly_distribution": hourly_traffic,
        "navigation_impact": {
            "collision_risk": collision_risk,
            "recommended_speed_adjustment": f"-{average_speed_reduction:.1f} knots" if average_speed_reduction > 0 else "None",
            "estimated_delay_minutes": int(average_speed_reduction * 60 / 20),  # Rough estimate
            "alternative_time_windows": [
                {"period": "00:00-05:00", "traffic": "Light", "recommendation": "Optimal"},
                {"period": "05:00-09:00", "traffic": "Increasing", "recommendation": "Acceptable"},
                {"period": "09:00-17:00", "traffic": "Heavy", "recommendation": "Avoid if possible"},
                {"period": "17:00-22:00", "traffic": "Decreasing", "recommendation": "Acceptable"},
                {"period": "22:00-00:00", "traffic": "Light", "recommendation": "Good"}
            ]
        },
        "alerts": []
    }
    
    # Add alerts based on conditions
    if collision_risk == "High":
        result["alerts"].append("High collision risk - maintain vigilant watch")
    if congestion_level == "High":
        result["alerts"].append("High traffic congestion - expect delays")
    if traffic_density > 6:
        result["alerts"].append("Dense traffic area - reduce speed as necessary")
    
    return result

@tool  
def get_traffic_forecast(
    route_segments: List[Dict],
    departure_date: str,
    vessel_speed_knots: float
) -> List[Dict]:
    """
    Get traffic forecast for entire route based on vessel progress.
    
    Args:
        route_segments: List of route segments
        departure_date: Departure date (YYYY-MM-DD)
        vessel_speed_knots: Vessel speed in knots
        
    Returns:
        Traffic forecast for all segments
    """
    
    departure = datetime.strptime(departure_date, "%Y-%m-%d")
    cumulative_hours = 0
    traffic_forecast = []
    
    for segment in route_segments:
        # Calculate arrival time at segment
        segment_date = departure + timedelta(hours=cumulative_hours)
        
        # Analyze traffic for this segment
        traffic = analyze_maritime_traffic(
            segment_id=segment["segment_id"],
            coordinates=segment["coordinates"],
            analysis_date=segment_date.strftime("%Y-%m-%d")
        )
        
        traffic["estimated_arrival"] = segment_date.isoformat()
        traffic["hours_from_departure"] = cumulative_hours
        
        # Adjust vessel speed based on traffic
        speed_reduction = traffic["traffic_summary"]["average_speed_reduction_knots"]
        effective_speed = max(vessel_speed_knots - speed_reduction, 10)  # Min 10 knots
        
        traffic["effective_speed_knots"] = effective_speed
        
        traffic_forecast.append(traffic)
        
        # Update cumulative time
        segment_distance = segment.get("distance_nm", 100)
        segment_hours = segment_distance / effective_speed
        cumulative_hours += segment_hours
    
    return traffic_forecast