"""Route calculation and analysis tools"""

import os
import pandas as pd
from math import radians, cos, sin, asin, sqrt
from typing import List, Dict, Tuple, Optional
from strands import tool
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in nautical miles."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c * 0.539957  # Convert km to nautical miles

@tool
def load_route_data(data_dir: str = "data") -> Dict:
    """
    Load all route data from CSV files.
    
    Args:
        data_dir: Directory containing the CSV files
        
    Returns:
        Dictionary containing all loaded dataframes
    """
    data_path = Path(data_dir)
    
    try:
        # Create sample data if files don't exist
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        
        # Create sample waypoints data
        if not os.path.exists(data_path / "maritime_waypoint_grid.csv"):
            waypoints_data = {
                "Waypoint_ID": ["WP_001", "WP_002", "WP_003", "WP_004", "WP_005"],
                "Latitude": [40.7128, 34.0522, 51.5074, -33.9249, 35.6762],
                "Longitude": [-74.0060, -118.2437, -0.1278, 18.4241, 139.6503],
                "Waypoint_Type": ["Port", "Port", "Port", "Port", "Port"],
                "Port_Name": ["New York", "Los Angeles", "London", "Cape Town", "Tokyo"]
            }
            pd.DataFrame(waypoints_data).to_csv(data_path / "maritime_waypoint_grid.csv", index=False)
        
        # Create sample routes data
        if not os.path.exists(data_path / "port_to_port_routes.csv"):
            routes_data = {
                "Route_ID": ["R_001", "R_002", "R_003", "R_004"],
                "Origin_Port": ["New York", "Los Angeles", "New York", "Cape Town"],
                "Destination_Port": ["Cape Town", "Tokyo", "London", "Tokyo"],
                "Route_Type": ["Transatlantic", "Transpacific", "Transatlantic", "Southern"],
                "Distance_NM": [6840, 5500, 3200, 7100],
                "Waypoint_IDs": ["WP_001,WP_004", "WP_002,WP_005", "WP_001,WP_003", "WP_004,WP_005"]
            }
            pd.DataFrame(routes_data).to_csv(data_path / "port_to_port_routes.csv", index=False)
        
        # Create sample carrier data
        if not os.path.exists(data_path / "Table1_Carrier_Route_Schedule.csv"):
            carrier_data = {
                "CARRIER_ID": ["CR_0001", "CR_0002", "CR_0003", "CR_0009"],
                "CARRIER_NAME": ["Ocean Express", "Global Maritime", "Sea Voyager", "Atlantic Shipping"],
                "SERVICE_TYPE": ["Container", "Bulk", "Tanker", "Container"],
                "ORIGIN_PORT": ["New York", "Los Angeles", "New York", "New York"],
                "DESTINATION_PORT": ["Cape Town", "Tokyo", "London", "Cape Town"],
                "AVG_SPEED_KNOTS": [22, 18, 20, 24]
            }
            pd.DataFrame(carrier_data).to_csv(data_path / "Table1_Carrier_Route_Schedule.csv", index=False)
        
        # Create sample port data
        if not os.path.exists(data_path / "Table2_Master_Port_Locations.csv"):
            port_data = {
                "PORT_CITY": ["New York", "Los Angeles", "London", "Cape Town", "Tokyo"],
                "PORT_CODE": ["USNYC", "USLAX", "GBLON", "ZACPT", "JPTYO"],
                "PORT_LATITUDE": [40.7128, 34.0522, 51.5074, -33.9249, 35.6762],
                "PORT_LONGITUDE": [-74.0060, -118.2437, -0.1278, 18.4241, 139.6503]
            }
            pd.DataFrame(port_data).to_csv(data_path / "Table2_Master_Port_Locations.csv", index=False)
        
        # Load data
        waypoints = pd.read_csv(data_path / "maritime_waypoint_grid.csv")
        routes = pd.read_csv(data_path / "port_to_port_routes.csv")
        carriers = pd.read_csv(data_path / "Table1_Carrier_Route_Schedule.csv")
        ports = pd.read_csv(data_path / "Table2_Master_Port_Locations.csv")
        
        return {
            "waypoints": waypoints,
            "routes": routes,
            "carriers": carriers,
            "ports": ports
        }
    except Exception as e:
        logger.error(f"Error loading route data: {e}")
        return {}

@tool
def find_routes_between_ports(
    origin_port: str,
    destination_port: str,
    data_dir: str = "data"
) -> List[Dict]:
    """
    Find all available routes between two ports.
    
    Args:
        origin_port: Name of the origin port
        destination_port: Name of the destination port
        data_dir: Directory containing route data
        
    Returns:
        List of available routes with details
    """
    data = load_route_data(data_dir)
    if not data:
        return []
    
    routes = data["routes"]
    waypoints = data["waypoints"]
    
    # Find routes matching origin and destination
    matching_routes = routes[
        (routes["Origin_Port"] == origin_port) & 
        (routes["Destination_Port"] == destination_port)
    ]
    
    route_details = []
    for _, route in matching_routes.iterrows():
        # Parse waypoint IDs
        waypoint_ids = route["Waypoint_IDs"].split(",") if pd.notna(route["Waypoint_IDs"]) else []
        
        # Get waypoint details
        route_waypoints = []
        total_distance = 0
        
        for i, wp_id in enumerate(waypoint_ids):
            wp = waypoints[waypoints["Waypoint_ID"] == wp_id.strip()]
            if not wp.empty:
                wp_data = wp.iloc[0]
                route_waypoints.append({
                    "waypoint_id": wp_data["Waypoint_ID"],
                    "type": wp_data["Waypoint_Type"],
                    "latitude": wp_data["Latitude"],
                    "longitude": wp_data["Longitude"],
                    "port_name": wp_data["Port_Name"] if pd.notna(wp_data["Port_Name"]) else None
                })
                
                # Calculate distance to next waypoint
                if i > 0:
                    prev_wp = route_waypoints[i-1]
                    distance = haversine_distance(
                        prev_wp["latitude"], prev_wp["longitude"],
                        wp_data["Latitude"], wp_data["Longitude"]
                    )
                    total_distance += distance
        
        # Generate intermediate waypoints if there are less than 4 waypoints
        if len(route_waypoints) < 2:
            # Route doesn't have enough waypoints to analyze
            continue
            
        elif len(route_waypoints) < 4:
            # Interpolate waypoints to get at least 4
            enriched_waypoints = [route_waypoints[0]]  # Start with first waypoint
            
            # Add intermediate points
            for i in range(len(route_waypoints) - 1):
                start = route_waypoints[i]
                end = route_waypoints[i+1]
                
                # Calculate number of points to add
                num_points = max(1, (4 - len(route_waypoints)))
                
                for j in range(1, num_points + 1):
                    fraction = j / (num_points + 1)
                    # Interpolate lat/lon
                    lat = start["latitude"] + fraction * (end["latitude"] - start["latitude"])
                    lon = start["longitude"] + fraction * (end["longitude"] - start["longitude"])
                    
                    enriched_waypoints.append({
                        "waypoint_id": f"{start['waypoint_id']}_int_{j}",
                        "type": "Intermediate",
                        "latitude": lat,
                        "longitude": lon,
                        "port_name": None
                    })
                
                enriched_waypoints.append(end)
            
            route_waypoints = enriched_waypoints
        
        # Divide route into segments (4 segments as specified)
        segments = []
        points_per_segment = max(1, len(route_waypoints) // 4)
        
        for i in range(0, len(route_waypoints), points_per_segment):
            segment_waypoints = route_waypoints[i:i+points_per_segment]
            if segment_waypoints:
                # Calculate segment distance
                segment_distance = 0
                for j in range(len(segment_waypoints) - 1):
                    start = segment_waypoints[j]
                    end = segment_waypoints[j+1]
                    segment_distance += haversine_distance(
                        start["latitude"], start["longitude"],
                        end["latitude"], end["longitude"]
                    )
                
                segments.append({
                    "segment_id": f"{route['Route_ID']}_seg_{len(segments)+1}",
                    "waypoints": segment_waypoints,
                    "coordinates": [(wp["latitude"], wp["longitude"]) for wp in segment_waypoints],
                    "distance_nm": segment_distance
                })
        
        # Use the route's distance if available, otherwise calculate
        if pd.notna(route.get("Distance_NM")):
            total_distance = route["Distance_NM"]
        else:
            # Sum segment distances
            total_distance = sum(segment["distance_nm"] for segment in segments)
        
        route_details.append({
            "route_id": route["Route_ID"],
            "route_type": route["Route_Type"],
            "total_distance_nm": round(total_distance, 2),
            "waypoint_count": len(route_waypoints),
            "segments": segments,
            "waypoints": route_waypoints
        })
    
    return route_details

@tool
def calculate_route_time(
    route: Dict,
    vessel_speed_knots: float,
    weather_impact: Optional[Dict] = None,
    traffic_impact: Optional[Dict] = None
) -> Dict:
    """
    Calculate estimated travel time for a route.
    
    Args:
        route: Route dictionary with waypoints
        vessel_speed_knots: Base vessel speed
        weather_impact: Weather impact on speed (optional)
        traffic_impact: Traffic impact on speed (optional)
        
    Returns:
        Time calculation details
    """
    base_time = route["total_distance_nm"] / vessel_speed_knots
    
    # Apply weather impact
    weather_delay = 0
    if weather_impact:
        wind_factor = weather_impact.get("average_wind_speed", 0) / 100
        weather_delay = base_time * wind_factor
    
    # Apply traffic impact  
    traffic_delay = 0
    if traffic_impact:
        congestion_factor = 0.1 if traffic_impact.get("congestion_level") == "High" else 0.05
        traffic_delay = base_time * congestion_factor
    
    total_time = base_time + weather_delay + traffic_delay
    
    return {
        "base_time_hours": round(base_time, 2),
        "weather_delay_hours": round(weather_delay, 2),
        "traffic_delay_hours": round(traffic_delay, 2),
        "total_time_hours": round(total_time, 2),
        "total_time_days": round(total_time / 24, 2),
        "effective_speed_knots": round(route["total_distance_nm"] / total_time, 2)
    }

@tool
def get_carrier_info(carrier_id: str, data_dir: str = "data") -> Optional[Dict]:
    """
    Get carrier information and capabilities.
    
    Args:
        carrier_id: Carrier identifier
        data_dir: Directory containing carrier data
        
    Returns:
        Carrier information dictionary
    """
    data = load_route_data(data_dir)
    if not data:
        return None
    
    carriers = data["carriers"]
    carrier = carriers[carriers["CARRIER_ID"] == carrier_id]
    
    if carrier.empty:
        return None
    
    carrier_data = carrier.iloc[0]
    return {
        "carrier_id": carrier_data["CARRIER_ID"],
        "carrier_name": carrier_data["CARRIER_NAME"],
        "avg_speed_knots": carrier_data["AVG_SPEED_KNOTS"],
        "service_type": carrier_data["SERVICE_TYPE"],
        "routes": carrier[["ORIGIN_PORT", "DESTINATION_PORT"]].to_dict('records')
    }