"""
Utility functions for handling transport-related operations.
"""

import re
import pandas as pd

from config.settings import MRT_LRT_DATA_PATH


def clean_station_prompt(prompt):
    """
    Extract station codes and lines from route information.
    
    Args:
        prompt (str): Text containing route information
        
    Returns:
        tuple: (station_dataframe, origin_station, destination_station)
    """
    # Segregate into multiple routes
    routes = []
    prompt_routes_pattern = r'Route .*?\\.'
    prompt_single_pattern = r'MRT station .*?\\.'
    prompt_routes = re.findall(prompt_routes_pattern, prompt)
    prompt_single = re.findall(prompt_single_pattern, prompt)
    
    if not prompt_single:
        for indiv_route in prompt_routes:
            routes.append(indiv_route)
    else:
        routes.append(prompt_single)
    
    # Loop to get info of all stations
    station_df = pd.DataFrame(columns=['stn_codes', 'stn_lines'])
    
    for i in range(len(routes)):
        # Get all stn_codes from prompt
        route_station = pd.DataFrame()
        pattern = r'\\b(?:[A-Z]{2}\\d{2}|[A-Z]{2}\\d{1})\\b'
        codes = re.findall(pattern, prompt)
        lines = [station[:2] + 'L' for station in codes]
        
        route_station = pd.DataFrame({
            'stn_codes': codes,
            'stn_lines': lines
        })
        
        station_df = pd.concat([station_df, route_station], ignore_index=True)
        
        if i == 0:
            origin = station_df.loc[0, 'stn_codes']
            destination = station_df.loc[len(station_df)-1, 'stn_codes']
    
    station_df = station_df.drop_duplicates(subset='stn_codes')
    return station_df, origin, destination


def clean_high_crowd_prompt(prompt, data_df):
    """
    Extract high crowd level information from prompt.
    
    Args:
        prompt (str): Text containing crowd information
        data_df (DataFrame): DataFrame to update
        
    Returns:
        DataFrame: Updated DataFrame with high crowd information
    """
    # Segregate into multiple routes
    high_crowd = []
    high_crowd_pattern = r'CROWD LEVEL HIGH .*?\\.'
    high_crowd_prompt = re.findall(high_crowd_pattern, prompt)
    
    if high_crowd_prompt is None:
        return None
    else:
        high_crowd.append(high_crowd_prompt)
    
    # Loop to get info of all stations
    pattern = r'\\b(?:[A-Z]{2}\\d{2}|[A-Z]{2}\\d{1})\\b'
    codes = re.findall(pattern, prompt)
    high_crowd_stn = pd.DataFrame({
        'stn_codes': codes,
    })
    
    data_df = pd.concat([data_df, high_crowd_stn], ignore_index=True)
    data_df = data_df.drop_duplicates(subset='stn_codes')
    
    return data_df


def clean_alert_prompt(prompt):
    """
    Extract station codes and lines from alert information.
    
    Args:
        prompt (str): Text containing alert information
        
    Returns:
        DataFrame: DataFrame with station codes and lines
    """
    # Extract station codes
    station_df = pd.DataFrame()
    pattern = r'\\b(?:[A-Z]{2}\\d{2}|[A-Z]{2}\\d{1})\\b'
    codes = re.findall(pattern, prompt)
    lines = [station[:2] + 'L' for station in codes]
    
    route_station = pd.DataFrame({
        'stn_codes': codes,
        'stn_lines': lines
    })
    
    station_df = pd.concat([station_df, route_station], ignore_index=True)
    station_df = station_df.drop_duplicates(subset='stn_codes')
    
    return station_df


def get_station_names(df, field=None):
    """
    Add station names to DataFrame based on station codes.
    
    Args:
        df (DataFrame): DataFrame containing station codes
        field (str, optional): Prefix for station column name
        
    Returns:
        DataFrame: Updated DataFrame with station names
    """
    input_csv = pd.read_csv(MRT_LRT_DATA_PATH)
    
    if field is None:
        col_name = 'Station'
    else:
        col_name = f'{field}_Station'
    
    df_copy = df.copy()
    
    for index, row in df_copy.iterrows():
        match = input_csv[input_csv['station_code'] == row['Station']]
        if not match.empty:
            station_code_name = f"{row['Station']} {match['full_name'].values[0]}"
            df_copy.at[index, 'Station'] = station_code_name
    
    df_copy.rename(columns={'Station': col_name}, inplace=True)
    return df_copy


def summarize_crowd(df):
    """
    Summarize crowd levels by station.
    
    Args:
        df (DataFrame): DataFrame containing crowd information
        
    Returns:
        str: Summary of crowd levels
    """
    grouped = df.groupby('CrowdLevel')['Station'].apply(lambda x: ', '.join(x)).reset_index()
    
    # Construct the summary string
    summary = ''
    for _, row in grouped.iterrows():
        summary += f"CROWD LEVEL {row['CrowdLevel'].split()[-1]} at these stations: {row['Station']}.\n "
    
    # Remove trailing comma and space
    summary = summary[:-2]
    return summary


def summarize_alerts(df):
    """
    Summarize service alerts by station.
    
    Args:
        df (DataFrame): DataFrame containing alert information
        
    Returns:
        str: Summary of service alerts
    """
    grouped = df.groupby('Status')['Station'].apply(lambda x: ', '.join(x)).reset_index()
    
    # Drop no issues
    grouped = grouped[grouped['Status'] != 'No train service issues at selected stations.']
    
    if not grouped.empty:
        # Construct the summary string
        summary = ''
        for _, row in grouped.iterrows():
            summary += f"{row['Status']} at these stations: {row['Station']}.\n"
        
        # Remove trailing newline
        summary = summary[:-1]
        return summary
    else:
        return 'No train service issues at selected stations.'


def summarize_nearest_taxi(df):
    """
    Summarize nearest taxi stands.
    
    Args:
        df (DataFrame): DataFrame containing taxi stand information
        
    Returns:
        str: Summary of nearest taxi stands
    """
    df = df.reset_index(drop=True)
    df = df.loc[:, ['Name', 'Distance']]
    df['Distance'] = df['Distance'].round(1).astype(str)
    
    summary = ''
    for index, row in df.iterrows():
        summary += f"{row['Name']} at {row['Distance']}m"
        if index != len(df) - 1:
            summary += "; "
        else:
            summary += "."
    
    return summary


def summarize_nearest_taxi_with_links(df):
    """
    Summarize nearest taxi stands with Google Maps links.
    
    Args:
        df (DataFrame): DataFrame containing taxi stand information
        
    Returns:
        str: Summary of nearest taxi stands with links
    """
    df = df.reset_index(drop=True)
    df = df.loc[:, ['Latitude', 'Longitude', 'Name', 'Distance']]
    df['Distance'] = df['Distance'].round(1).astype(str)
    
    summary = ''
    for index, row in df.iterrows():
        summary += f"{row['Name']} at {row['Distance']}m (Link: https://www.google.com/maps?q={row['Latitude']},{row['Longitude']})"
        if index != len(df) - 1:
            summary += " ; "
        else:
            summary += " ."
    
    return summary


def summarize_time(df):
    """
    Summarize crowd levels by time.
    
    Args:
        df (DataFrame): DataFrame containing time-based crowd information
        
    Returns:
        str: Summary of crowd levels by time
    """
    # Construct the summary string
    summary = ''
    for _, row in df.iterrows():
        summary += f"CROWD LEVEL at {row['Station']} is {row['CrowdLevel'].split()[-1]} at these timings: {row['Start']}.\n "
    
    # Remove trailing newline and space
    summary = summary[:-2]
    return summary


def summarize_volume_time(df):
    """
    Summarize crowd volume by time.
    
    Args:
        df (DataFrame): DataFrame containing time-based volume information
        
    Returns:
        str: Summary of crowd volume by time
    """
    grouped_df = df.groupby(['DAY_TYPE', 'Station', 'CrowdVolume'], observed=False)['Start'].apply(list).reset_index()
    grouped = grouped_df.dropna()
    
    summary = ''
    # Construct the summary string
    for day in grouped['DAY_TYPE'].unique():
        summary += f"On {day} : "
        for station in grouped['Station'].unique():
            summary += f"CROWD VOLUME at {station} is "
            count = 0
            for volume in grouped['CrowdVolume'].unique():
                timings = grouped[(grouped['DAY_TYPE'] == day) & 
                                  (grouped['Station'] == station) & 
                                  (grouped['CrowdVolume'] == volume)]['Start'].tolist()
                timings_str = str(timings).strip('[]')
                
                if len(timings_str) > 0:
                    if count > 0:
                        summary += ", "
                    summary += f"{volume} at these timings: {timings_str}"
                if volume == grouped['CrowdVolume'].unique()[-1]:
                    summary += ".\n "
                count += 1
    
    # Remove trailing newline and space
    summary = summary[:-2]
    return summary