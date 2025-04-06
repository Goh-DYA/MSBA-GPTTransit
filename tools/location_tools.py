"""
LangChain tools for location-based operations.
"""

import pandas as pd
from langchain.agents import tool

from config.settings import TAXI_STANDS_DATA_PATH
from api.onemap_api import get_gps_coordinates
from utils.location_utils import calculate_taxi_distances
from utils.transport_utils import summarize_nearest_taxi, summarize_nearest_taxi_with_links


@tool
def getGPS(query: str) -> str:
    """
    Get the latitude and longitude coordinates for a location.
    
    Args:
        query (str): Location or postal code or address or road name
        
    Returns:
        str: GPS coordinates and address information
    """
    lat, lon, address = get_gps_coordinates(query)
    
    if lat is not None:
        output_msg = f"Latitude: {lat}\nLongitude: {lon}\nAddress: {address}"
        return output_msg
    else:
        output_msg = "No results were found. Ensure that the input is a valid location, postal code, address or road name."
        return output_msg


@tool
def checkNearestTaxiStands(input_location: str) -> str:
    """
    Find the location of and distance to the nearest taxi stands.
    
    Args:
        input_location (str): Location or postal code or address or road name
        
    Returns:
        str: Information about the nearest taxi stands
    """
    # Get GPS coordinates for the location
    lat, lon, address = get_gps_coordinates(input_location)
    
    if lat is not None:
        # Calculate distance to taxi stands
        taxi_df = pd.read_csv(TAXI_STANDS_DATA_PATH)
        taxi_df = calculate_taxi_distances(lat, lon, taxi_df)

        # Summarize the nearest taxi stands
        nearest_taxis = summarize_nearest_taxi_with_links(taxi_df.nsmallest(3, 'Distance'))
        summary = f'Nearest taxi stands at {input_location} are : {nearest_taxis}'
        
        return summary
    else:
        return "Error: No results were found. Ensure that the input is a valid location, postal code, address or road name."


@tool
def checkNearestAttractions(input_location: str) -> str:
    """
    Get recommendations for nearby restaurants or attractions.
    
    Args:
        input_location (str): Location or postal code or address or road name
        
    Returns:
        str: Google Maps links to nearby restaurants and attractions
    """
    # Get GPS coordinates for the location
    lat, lon, address = get_gps_coordinates(input_location)
    
    if lat is not None:
        # Create Google Maps links for restaurants and attractions
        summary = (
            f'If you are at {address}, try some local delights at '
            f'http://www.google.com/maps/search/Restaurant/@{lat},{lon},16z/data=!3m1!4b1?entry=ttu '
            f'and visit attractions at '
            f'http://www.google.com/maps/search/Things+to+do/@{lat},{lon},16z/data=!3m1!4b1?entry=ttu .'
        )
        
        return summary
    else:
        return "Error: No results were found. Ensure that the input is a valid location, postal code, address or road name."