"""
Utility functions for location-based operations.
"""

import pandas as pd
from math import radians, sin, cos, sqrt, atan2

from config.settings import MRT_LRT_DATA_PATH


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    
    Args:
        lat1 (float): Latitude of point 1
        lon1 (float): Longitude of point 1
        lat2 (float): Latitude of point 2
        lon2 (float): Longitude of point 2
        
    Returns:
        float: Distance in meters
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    # Radius of Earth in kilometers
    distance = 6371 * c

    # Return distance in meters
    return distance * 1000


def get_station_coordinates(station_code):
    """
    Get the coordinates and name of an MRT/LRT station.
    
    Args:
        station_code (str): Station code (e.g., 'NS1')
        
    Returns:
        tuple: (latitude, longitude, station_name)
    """
    # Read station data
    station_df = pd.read_csv(MRT_LRT_DATA_PATH)
    
    # Find station data
    station_data = station_df[station_df['station_code'] == station_code]
    
    if station_data.empty:
        return None, None, None
    
    # Extract data
    station_lat = station_data['lat'].values[0]
    station_lon = station_data['lng'].values[0]
    station_name = f"{station_code} {station_data['full_name'].values[0]}"
    
    return station_lat, station_lon, station_name


def calculate_taxi_distances(place_lat, place_lon, taxi_df):
    """
    Calculate distances between a given location and taxi stands.
    
    Args:
        place_lat (float): Latitude of the reference point
        place_lon (float): Longitude of the reference point
        taxi_df (DataFrame): DataFrame containing taxi stand data
        
    Returns:
        DataFrame: Updated DataFrame with distance information
    """
    # Calculate distance for each taxi stand
    distances = []
    
    for _, row in taxi_df.iterrows():
        taxi_lat = row['Latitude']
        taxi_lon = row['Longitude']
        distance = haversine(place_lat, place_lon, taxi_lat, taxi_lon)
        distances.append(distance)
    
    # Add distances to DataFrame
    taxi_df_with_distances = taxi_df.copy()
    taxi_df_with_distances['Distance'] = pd.Series(distances)
    
    return taxi_df_with_distances