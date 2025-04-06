"""
LangChain tools for crowd-related operations.
"""

import pandas as pd
from langchain.agents import tool

from api.lta_api import get_crowd_request
from utils.time_utils import clean_time_prompt
from utils.crowd_utils import (
    clean_realtime_crowd, 
    clean_crowd,
    clean_forecast_volume,
    clean_time_crowd
)
from config.settings import TRANSPORT_NODE_DATA_PATH
from tools.transport_tools import get_public_transport_route_concise
from utils.transport_utils import clean_station_prompt


@tool
def checkRealTimeCrowd(input_prompt: str) -> str:
    """
    Find the real time and current MRT train platform crowdedness level.
    
    Args:
        input_prompt (str): Input in format 'station_name' OR 'start_station,end_station'
        
    Returns:
        str: Real-time crowd levels at the specified stations
    """
    # Clean prompt
    text_input_prompt, _ = clean_time_prompt(input_prompt)
    prompt = get_public_transport_route_concise(text_input_prompt)
    
    if "Error" not in prompt:
        prompt_stn_df, _, _ = clean_station_prompt(prompt)
    
        # Get data
        url_type = 'RealTime'
        realtime_df = pd.DataFrame()
        
        for line in (prompt_stn_df['stn_lines'].unique()):
            response = get_crowd_request(url_type, line)
            
            if response is not None and 'error' not in response:
                json_df = clean_realtime_crowd(response)
                realtime_df = pd.concat([realtime_df, json_df])
            else:
                return "Error: Failed to fetch real-time crowd data. Please try again later."
        
        realtime_crowd = clean_crowd(realtime_df, prompt_stn_df)
        
        if realtime_crowd is not None:
            return realtime_crowd
        else:
            return "No live crowd data available. Please try again later."
    else:
        return f"{prompt}"


@tool
def checkForecastVolume(input_prompt: str) -> str:
    """
    Find the forecasted or predicted future MRT train platform crowdedness level.
    
    Args:
        input_prompt (str): Input with station and time information in format:
        'station_name;DD-MM-YYYY,HH:MM' OR 'start_station,end_station;DD-MM-YYYY,HH:MM'
        
    Returns:
        str: Forecast crowd levels at the specified stations and times
    """
    # Clean prompt
    text_input_prompt, datetime_input_prompt = clean_time_prompt(input_prompt)
    prompt = get_public_transport_route_concise(text_input_prompt)
    
    if "Error" not in prompt:
        prompt_stn_df, origin, destination = clean_station_prompt(prompt)
        
        # Use only origin and destination for forecast
        prompt_stn_df = pd.DataFrame({
            'stn_codes': [origin, destination],
            'stn_lines': [(origin[:2] + 'L'), (destination[:2] + 'L')]
        })

        # Load volume data
        data_df = pd.read_csv(TRANSPORT_NODE_DATA_PATH)
        data_df = clean_csv(data_df)

        # Get crowd volume forecast
        crowd_volume = clean_forecast_volume(data_df, prompt_stn_df, datetime_input_prompt)
        
        if crowd_volume is not None:
            # Check if date is a weekday/weekend
            from utils.time_utils import check_weekday_or_weekend
            weekday_weekend_string = check_weekday_or_weekend(datetime_input_prompt)
            crowd_volume = weekday_weekend_string + crowd_volume
            
            return crowd_volume
        else:
            return "No crowd volume data available. Please try again later."
    else:
        return f"{prompt}"


def clean_csv(df, where=None):
    """
    Helper function to clean CSV data by splitting station codes with '/' character.
    
    Args:
        df (DataFrame): DataFrame to clean
        where (str, optional): Prefix for column names
        
    Returns:
        DataFrame: Cleaned DataFrame
    """
    if where is None:
        col_name = 'PT_CODE'
    else:
        col_name = f'{where}_PT_CODE'
    
    modified_rows = []
    
    for _, row in df.iterrows():
        if '/' in row['PT_CODE']:
            codes = row['PT_CODE'].split('/')
            
            for code in codes:
                new_row = row.copy()
                new_row['PT_CODE'] = code
                modified_rows.append(new_row)
        else:
            modified_rows.append(row)
    
    modified_df = pd.DataFrame(modified_rows)
    modified_df.rename(columns={'PT_CODE': col_name}, inplace=True)
    
    return modified_df