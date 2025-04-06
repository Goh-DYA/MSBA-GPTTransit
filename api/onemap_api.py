"""
OneMap API client for location-based services.
"""

import requests
from datetime import datetime

from config.settings import ONEMAP_API_KEY, ONEMAP_BASE_URL, MRT_LRT_DATA_PATH
from config.settings import MAX_WALK_DISTANCE, NUM_ITINERARIES


def get_gps_coordinates(query):
    """
    Get GPS coordinates for a location.
    
    Args:
        query (str): Search query (location, postal code, address, etc.)
    
    Returns:
        tuple: (latitude, longitude, address) or (None, None, None) if not found
    """
    url = f"{ONEMAP_BASE_URL}/common/elastic/search?searchVal={query}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
    headers = {"Content-Type": "application/json"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        api_output = response.json()
        
        if api_output["found"] > 0:
            result = api_output["results"][0]  # Extract the first result
            latitude = float(result["LATITUDE"])
            longitude = float(result["LONGITUDE"])
            address = result["ADDRESS"]
            
            return latitude, longitude, address
        else:
            return None, None, None
    else:
        return None, None, None


def get_public_transport_route(start_coords, end_coords, transit_mode="RAIL"):
    """
    Get public transport routes between two points.
    
    Args:
        start_coords (tuple): (latitude, longitude) of start point
        end_coords (tuple): (latitude, longitude) of end point
        transit_mode (str): Mode of transport (RAIL, BUS, etc.)
        
    Returns:
        dict: JSON response from API
    """
    # Extract coordinates
    lat_start, lng_start = start_coords
    lat_end, lng_end = end_coords
    
    # Define parameters for API request
    route_type = "pt"
    date = datetime.today().strftime("%m-%d-%Y")
    hour = '{:02d}'.format(datetime.now().hour)
    minute = '{:02d}'.format(datetime.now().minute)
    
    # Construct URL for API request
    url = (
        f"{ONEMAP_BASE_URL}/public/routingsvc/route"
        f"?start={lat_start}%2C{lng_start}"
        f"&end={lat_end}%2C{lng_end}"
        f"&routeType={route_type}"
        f"&date={date}"
        f"&time={hour}%3A{minute}%3A00"
        f"&mode={transit_mode}"
        f"&maxWalkDistance={MAX_WALK_DISTANCE}"
        f"&numItineraries={NUM_ITINERARIES}"
    )
    
    # Define headers for API request
    headers = {
        "Authorization": ONEMAP_API_KEY
    }
    
    # Make API request
    response = requests.get(url, headers=headers)
    
    # Return response
    return response.json() if response.ok else None