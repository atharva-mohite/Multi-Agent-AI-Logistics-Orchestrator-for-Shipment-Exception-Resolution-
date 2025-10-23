"""Weather Forecast Tool for Maritime Routes"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from strands import tool
import logging

logger = logging.getLogger(__name__)

@tool
def get_weather_forecast(
    coordinates: List[Tuple[float, float]], 
    forecast_date: str,
    segment_id: str
) -> Dict:
    """
    Get weather forecast for maritime route coordinates.
    
    Args:
        coordinates: List of (latitude, longitude) tuples for the segment
        forecast_date: Date for the forecast (YYYY-MM-DD format)
        segment_id: Identifier for the route segment
    
    Returns:
        Weather forecast data for the coordinates
    """
    
    logger.debug(f"Generating weather forecast for segment {segment_id} on {forecast_date}")
    
    # Parse the forecast date
    try:
        date_obj = datetime.strptime(forecast_date, "%Y-%m-%d")
    except ValueError:
        date_obj = datetime.now()
    
    # Generate plausible weather conditions
    weather_conditions = ["Clear", "Partly Cloudy", "Overcast", "Light Rain", "Heavy Rain", "Fog", "Stormy"]
    sea_states = ["Calm", "Slight", "Moderate", "Rough", "Very Rough", "High"]
    
    # Generate weather for each coordinate
    forecasts = []
    for lat, lon in coordinates:
        # Simulate weather patterns based on latitude
        temp_base = 25 - abs(lat) / 4  # Temperature decreases with latitude
        
        condition = random.choice(weather_conditions)
        severity_factor = 1.0
        
        # Adjust metrics based on condition
        if condition == "Stormy":
            severity_factor = 2.5
        elif condition == "Heavy Rain":
            severity_factor = 2.0
        elif condition == "Fog":
            severity_factor = 1.5
        
        forecast = {
            "location": {"lat": lat, "lon": lon},
            "date": forecast_date,
            "condition": condition,
            "description": f"{condition} conditions with {random.choice(sea_states).lower()} seas",
            "metrics": {
                "temperature_celsius": round(temp_base + random.uniform(-5, 5), 1),
                "humidity_percent": random.randint(40, 95),
                "wind_speed_knots": round(random.uniform(5, 30) * severity_factor, 1),
                "wave_height_meters": round(random.uniform(0.5, 4) * severity_factor, 1),
                "visibility_km": round(random.uniform(2, 20) / severity_factor, 1),
                "pressure_mb": random.randint(990, 1030),
                "sea_state": random.choice(sea_states)
            },
            "warnings": []
        }
        
        # Add warnings for severe conditions
        if forecast["metrics"]["wind_speed_knots"] > 40:
            forecast["warnings"].append("High wind warning")
        if forecast["metrics"]["wave_height_meters"] > 5:
            forecast["warnings"].append("High seas warning")
        if forecast["metrics"]["visibility_km"] < 2:
            forecast["warnings"].append("Low visibility warning")
        if condition == "Stormy":
            forecast["warnings"].append("Storm warning - consider route diversion")
        
        forecasts.append(forecast)
    
    # Generate segment summary
    avg_wind = sum(f["metrics"]["wind_speed_knots"] for f in forecasts) / len(forecasts) if forecasts else 0
    avg_waves = sum(f["metrics"]["wave_height_meters"] for f in forecasts) / len(forecasts) if forecasts else 0
    
    risk_level = "Low"
    if avg_wind > 35 or avg_waves > 4:
        risk_level = "High"
    elif avg_wind > 25 or avg_waves > 3:
        risk_level = "Medium"
    
    return {
        "segment_id": segment_id,
        "forecast_date": forecast_date,
        "points_analyzed": len(coordinates),
        "forecasts": forecasts,
        "segment_summary": {
            "predominant_condition": max(set([f["condition"] for f in forecasts]), 
                                        key=[f["condition"] for f in forecasts].count) if forecasts else "Unknown",
            "average_wind_speed": round(avg_wind, 1),
            "average_wave_height": round(avg_waves, 1),
            "risk_level": risk_level,
            "recommendation": f"Weather conditions are {risk_level.lower()} risk for navigation"
        }
    }

@tool
def get_extended_forecast(
    route_segments: List[Dict],
    departure_date: str,
    vessel_speed_knots: float
) -> List[Dict]:
    """
    Get extended weather forecast for entire route based on vessel speed.
    
    Args:
        route_segments: List of route segments with coordinates
        departure_date: Departure date (YYYY-MM-DD)
        vessel_speed_knots: Vessel speed in knots
        
    Returns:
        Extended forecast for all segments
    """
    
    departure = datetime.strptime(departure_date, "%Y-%m-%d")
    cumulative_distance = 0
    extended_forecast = []
    
    for segment in route_segments:
        # Calculate when vessel will reach this segment
        hours_to_segment = cumulative_distance / vessel_speed_knots if vessel_speed_knots > 0 else 0
        segment_date = departure + timedelta(hours=hours_to_segment)
        
        # Get weather for this segment
        forecast = get_weather_forecast(
            coordinates=segment.get("coordinates", []),
            forecast_date=segment_date.strftime("%Y-%m-%d"),
            segment_id=segment.get("segment_id", "unknown")
        )
        
        forecast["estimated_arrival"] = segment_date.isoformat()
        forecast["hours_from_departure"] = round(hours_to_segment, 1)
        
        extended_forecast.append(forecast)
        cumulative_distance += segment.get("distance_nm", 100)  # Default 100nm per segment
    
    return extended_forecast