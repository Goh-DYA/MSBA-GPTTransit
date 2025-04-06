"""
LTA DataMall API client for fetching transport-related data.
"""

import requests
import pandas as pd

from config.settings import LTA_API_KEY, LTA_BASE_URL


def get_crowd_request(url_type, train_line):
    """
    Get crowd data from LTA API.
    
    Args:
        url_type (str): Type of crowd data ('RealTime' or 'Forecast')
        train_line (str): Train line code (e.g., 'NSL', 'EWL')
        
    Returns:
        dict: JSON response from API or error message
    """
    headers = {
        "AccountKey": LTA_API_KEY
    }
    
    url = f"{LTA_BASE_URL}/PCD{url_type}?TrainLine={train_line}"
    
    response = requests.get(url, headers=headers)
    
    # Check for response
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch data (status code: {response.status_code}), please try again later."}


def get_data_request(url_type):
    """
    Get various types of transit data from LTA API.
    
    Args:
        url_type (str): Type of data to fetch ('vol_by_stn', 'vol_to_fro', 'alert')
        
    Returns:
        dict: JSON response from API or None if request failed
    """
    # URLs
    vol_by_stn_url = f"{LTA_BASE_URL}/PV/Train"
    vol_to_fro_url = f"{LTA_BASE_URL}/PV/ODTrain?$skip=500"
    alert_url = f"{LTA_BASE_URL}/TrainServiceAlerts"

    if url_type == "vol_by_stn":
        url = vol_by_stn_url
    elif url_type == 'vol_to_fro':
        url = vol_to_fro_url
    elif url_type == 'alert':
        url = alert_url
    else:
        return None
    
    headers = {
        "AccountKey": LTA_API_KEY
    }
    
    response = requests.get(url, headers=headers)
    
    # Check for response
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data (status code: {response.status_code}), please try again later.")
        return None


def get_service_status(data):
    """
    Extract service status information from API response.
    
    Args:
        data (dict): API response data
        
    Returns:
        DataFrame: Service status information
    """
    if not data or "value" not in data:
        return pd.DataFrame()
    
    status = data["value"]["Status"]
    affected_segments = data["value"]["AffectedSegments"]
    messages = data["value"]["Message"]
    
    # Extracting affected segments information
    lines = [segment["Line"] for segment in affected_segments]
    directions = [segment["Direction"] for segment in affected_segments]
    stations = [segment["Stations"] for segment in affected_segments]
    free_public_bus = [segment["FreePublicBus"] for segment in affected_segments]
    free_mrt_shuttle = [segment["FreeMRTShuttle"] for segment in affected_segments]
    mrt_shuttle_direction = [segment["MRTShuttleDirection"] for segment in affected_segments]
    
    # Extracting message information
    content = [msg["Content"] for msg in messages]
    created_date = [msg["CreatedDate"] for msg in messages]
    
    # Create DataFrame
    df = pd.DataFrame({
        "Status": status,
        "Line": lines,
        "Direction": directions,
        "Stations": stations,
        "FreePublicBus": free_public_bus,
        "FreeMRTShuttle": free_mrt_shuttle,
        "MRTShuttleDirection": mrt_shuttle_direction,
        "MessageContent": content,
        "CreatedDate": created_date
    })
    
    return df


def validate_station_alert(data_df, station_code):
    """
    Check if a station is affected by a service alert.
    
    Args:
        data_df (DataFrame): DataFrame containing alert data
        station_code (str): Station code to check
        
    Returns:
        str: Status message for the station
    """
    import re
    
    # Normalize station code (remove leading zero in single-digit station numbers)
    if len(station_code) >= 3 and station_code[2] == '0':
        station_code = station_code[:2] + station_code[3:]
    
    station_line = station_code[:2] + 'L'
    status = "No train service issues at selected stations."
    
    for index, row in data_df.iterrows():
        if station_code in row['Stations']:
            service_message = data_df.loc[index, 'MessageContent']
            
            # Clean service_message
            split_strings = re.split(r'(\\d{4}hrs :)', service_message)
            combined_strings = []
            current_string = ''
            
            for string in split_strings:
                if string.endswith('hrs :'):
                    if current_string:
                        combined_strings.append(current_string.strip())
                    current_string = string
                else:
                    current_string += string
            
            if current_string:
                combined_strings.append(current_string.strip())
            
            for string in combined_strings:
                if station_line in string:
                    status = string
                    break
            break
    
    return status