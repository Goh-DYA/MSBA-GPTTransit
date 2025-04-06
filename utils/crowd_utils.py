"""
Utility functions for handling crowd level data.
"""

import pandas as pd
from datetime import timedelta


def clean_forecast_crowd(json_obj):
    """
    Clean JSON data for forecast crowd levels.
    
    Args:
        json_obj (dict): JSON response containing forecast crowd data
        
    Returns:
        DataFrame: Cleaned DataFrame of forecast crowd data
    """
    # Clean json data
    platform_data = []
    
    for entry in json_obj['value']:
        date = entry['Date']
        for station in entry['Stations']:
            station_name = station['Station']
            for interval in station['Interval']:
                interval_data = {
                    'Date': date,
                    'Station': station_name,
                    'Start': interval['Start'],
                    'CrowdLevel': interval['CrowdLevel']
                }
                platform_data.append(interval_data)
    
    df = pd.DataFrame(platform_data)
    df['Start'] = pd.to_datetime(df['Start']).dt.time
    df.drop(columns=["Date"], inplace=True)
    
    return df


def clean_realtime_crowd(json_obj):
    """
    Clean JSON data for real-time crowd levels.
    
    Args:
        json_obj (dict): JSON response containing real-time crowd data
        
    Returns:
        DataFrame: Cleaned DataFrame of real-time crowd data
    """
    # Clean json data
    df = pd.DataFrame(json_obj['value'])
    df['StartTime'] = pd.to_datetime(df['StartTime']).dt.time
    df.drop(columns=["EndTime"], inplace=True)
    
    return df


def clean_time_crowd(data_df, prompt_df, date_time):
    """
    Filter crowd data by time and station.
    
    Args:
        data_df (DataFrame): DataFrame containing crowd data
        prompt_df (DataFrame): DataFrame containing station data
        date_time (str): Date and time string
        
    Returns:
        str: Summary of crowd levels
    """
    from utils.time_utils import split_date_time
    from utils.transport_utils import summarize_crowd, get_station_names
    
    # Filter for station
    crowd = []
    day, time = split_date_time(date_time)
    
    for _, row in data_df.iterrows():
        if row['Station'] in prompt_df['stn_codes'].values:
            if (time-timedelta(minutes=30)).time() <= row['Start'] <= (time+timedelta(minutes=30)).time():
                crowd.append(row)
    
    # Clean output
    crowd_df = pd.DataFrame(crowd)
    
    if crowd_df.empty:
        return "No crowd data available for the selected time and stations."
    
    crowd_df.reset_index(drop=True, inplace=True)
    crowd_df.drop(columns=["Start"], inplace=True)
    crowd_df.drop_duplicates(subset=['Station', 'CrowdLevel'], inplace=True)
    
    check_crowd_df = pd.DataFrame(columns=['Station', 'CrowdLevel'])
    
    for station in crowd_df['Station'].unique():
        station_df = crowd_df[crowd_df['Station'] == station]
        crowd_levels = []

        # Arrange 'CrowdLevel' values by the order 'l', 'm', 'h'
        for level in ['l', 'm', 'h']:
            # Append values for current 'CrowdLevel' if present
            if level in station_df['CrowdLevel'].values:
                crowd_levels.append(level)
        
        current_crowd = pd.DataFrame({
            'Station': [station],
            'CrowdLevel': [crowd_levels]
        })
        
        check_crowd_df = pd.concat([check_crowd_df, current_crowd])
    
    check_crowd_df['CrowdLevel'] = check_crowd_df['CrowdLevel'].apply(replace_crowd_levels)
    check_crowd_df.reset_index(drop=True, inplace=True)
    check_crowd_df = get_station_names(check_crowd_df, None)
    
    crowd_string = summarize_crowd(check_crowd_df)
    return crowd_string


def clean_crowd(data_df, prompt_df):
    """
    Filter crowd data by station.
    
    Args:
        data_df (DataFrame): DataFrame containing crowd data
        prompt_df (DataFrame): DataFrame containing station data
        
    Returns:
        str: Summary of crowd levels
    """
    from utils.transport_utils import summarize_crowd, get_station_names
    
    # Filter for station
    crowd = []
    
    for _, row in data_df.iterrows():
        # Check if the station code from data_df is in prompt_df's 'stn_codes' column
        if row['Station'] in prompt_df['stn_codes'].values:
            # Append the row from data_df to matched_data
            crowd.append(row)
    
    if not crowd:
        return "No crowd data available for the selected stations."
    
    # Clean output
    crowd_df = pd.DataFrame(crowd)
    crowd_df.reset_index(drop=True, inplace=True)
    
    crowd_df['CrowdLevel'] = crowd_df['CrowdLevel'].replace({
        'l': 'CROWD LEVEL LOW',
        'm': 'CROWD LEVEL MODERATE',
        'h': 'CROWD LEVEL HIGH'
    })
    
    crowd_df.drop(columns=["StartTime"], inplace=True)
    crowd_df = get_station_names(crowd_df, None)
    
    crowd_string = summarize_crowd(crowd_df)
    return crowd_string


def replace_crowd_levels(levels):
    """
    Convert crowd level codes to readable text.
    
    Args:
        levels (list): List of crowd level codes
        
    Returns:
        str: Human-readable crowd level description
    """
    if levels == ['l']:
        return 'CROWD LEVEL LOW'
    elif levels == ['m']:
        return 'CROWD LEVEL MODERATE'
    elif levels == ['h']:
        return 'CROWD LEVEL HIGH'
    elif levels == ['l', 'm']:
        return 'CROWD LEVEL LOW TO MODERATE'
    elif levels == ['m', 'h']:
        return 'CROWD LEVEL MODERATE TO HIGH'
    elif levels == ['l', 'm', 'h']:
        return 'CROWD LEVEL LOW TO HIGH'
    else:
        return str(levels)


def clean_crowd_time(data_df, prompt_df, date_time):
    """
    Filter crowd data by time range and station.
    
    Args:
        data_df (DataFrame): DataFrame containing crowd data
        prompt_df (DataFrame): DataFrame containing station data
        date_time (str): Date and time string
        
    Returns:
        str: Summary of crowd levels by time
    """
    from utils.time_utils import split_date_time
    from utils.transport_utils import summarize_time, get_station_names
    from datetime import datetime
    
    # Filter for station
    crowd = []
    day, time = split_date_time(date_time)
    
    # Check if user input an actual time (+- 1.5hrs), else 7am - 10pm
    current_time = datetime.strptime((datetime.now().strftime("%H:%M")), "%H:%M")
    
    if time != current_time:
        start_check_time = (time-timedelta(minutes=90)).time()
        if start_check_time <= datetime.strptime('07:00', '%H:%M').time():
            start_check_time = datetime.strptime('07:00', '%H:%M').time()
        
        end_check_time = (time+timedelta(minutes=30)).time()
        if end_check_time >= datetime.strptime('22:00', '%H:%M').time():
            end_check_time = datetime.strptime('22:00', '%H:%M').time()
    else:
        start_check_time = datetime.strptime('07:00', '%H:%M').time()
        end_check_time = datetime.strptime('22:00', '%H:%M').time()
    
    # Find station
    for _, row in data_df.iterrows():
        if row['Station'] in prompt_df['stn_codes'].values:
            if start_check_time <= row['Start'] <= end_check_time:
                crowd.append(row)
    
    if not crowd:
        return "No crowd data available for the selected time range and stations."
    
    # Clean output
    crowd_df = pd.DataFrame(crowd)
    crowd_df['Start'] = crowd_df['Start'].apply(lambda x: x.strftime('%H:%M'))
    crowd_df.reset_index(drop=True, inplace=True)
    
    all_time_df = pd.DataFrame()
    
    for station in crowd_df['Station'].unique():
        station_df = crowd_df[crowd_df['Station'] == station]
        current_stn_df = station_df.groupby(['Station', 'CrowdLevel'])['Start'].apply(list).reset_index()
        
        # Arrange order 'l-m-h'
        current_stn_df['CrowdLevel'] = pd.Categorical(current_stn_df['CrowdLevel'], categories=['l', 'm', 'h'], ordered=True)
        current_stn_df = current_stn_df.sort_values('CrowdLevel')
        
        all_time_df = pd.concat([all_time_df, current_stn_df])
    
    all_time_df['CrowdLevel'] = all_time_df['CrowdLevel'].replace({
        'l': 'LOW',
        'm': 'MODERATE',
        'h': 'HIGH'
    })
    
    all_time_df.reset_index(drop=True, inplace=True)
    all_time_df = get_station_names(all_time_df, None)
    
    time_string = summarize_time(all_time_df)
    return time_string


def clean_forecast_volume(data_df, prompt_df, date_time):
    """
    Filter volume data by time range and station for forecasting.
    
    Args:
        data_df (DataFrame): DataFrame containing volume data
        prompt_df (DataFrame): DataFrame containing station data
        date_time (str): Date and time string
        
    Returns:
        str: Summary of forecast volume by time
    """
    from utils.time_utils import split_date_time
    from utils.transport_utils import summarize_volume_time, get_station_names
    from datetime import datetime
    from config.settings import PASSENGER_UPPER_THRESHOLD, PASSENGER_LOWER_THRESHOLD
    
    # Clean date
    day, time = split_date_time(date_time)
    data_df.rename(columns={'PT_CODE': 'Station', 'TIME_PER_HOUR': 'Start'}, inplace=True)
    
    # Check if user input an actual time (+- 2hrs), else 7am - 10pm
    current_time = datetime.strptime((datetime.now().strftime("%H:%M")), "%H:%M")
    
    if time != current_time:
        start_check_time = time.hour - 2
        if start_check_time <= 7:
            start_check_time = 7
        
        end_check_time = time.hour + 2
        if end_check_time >= 22:
            end_check_time = 22
    else:
        start_check_time = 7
        end_check_time = 22
    
    selected_list = []
    
    # Find station
    for _, row in data_df.iterrows():
        if row['Station'] in prompt_df['stn_codes'].values:
            if start_check_time <= row['Start'] <= end_check_time:
                selected_list.append(row)
    
    if not selected_list:
        return "No forecast data available for the selected time range and stations."
    
    # Check crowd volume
    selected_list_df = pd.DataFrame(selected_list)
    selected_list_df = selected_list_df.reset_index(drop=True)
    
    selected_list_df['Passenger_Volume'] = selected_list_df['TOTAL_TAP_IN_VOLUME'] + selected_list_df['TOTAL_TAP_OUT_VOLUME']
    
    for i in range(len(selected_list_df)):
        passenger_volume = selected_list_df.loc[i, 'Passenger_Volume']
        
        if passenger_volume > PASSENGER_UPPER_THRESHOLD:
            selected_list_df.loc[i, 'CrowdVolume'] = 'HIGH'
        elif passenger_volume < PASSENGER_LOWER_THRESHOLD:
            selected_list_df.loc[i, 'CrowdVolume'] = 'LOW'
        else:
            selected_list_df.loc[i, 'CrowdVolume'] = 'MODERATE'
    
    selected_list_df = selected_list_df.loc[:, ['Station', 'CrowdVolume', 'Passenger_Volume', 'Start', 'DAY_TYPE']]
    
    all_volume_df = pd.DataFrame()
    
    for station in selected_list_df['Station'].unique():
        station_df = selected_list_df[selected_list_df['Station'] == station]
        current_stn_df = station_df.groupby(['Station', 'CrowdVolume', 'DAY_TYPE'])['Start'].apply(list).reset_index()
        
        current_stn_df['Start'] = current_stn_df['Start'].apply(lambda hours: [f"{hour:02d}:00" for hour in hours])
        current_stn_df['Start'] = current_stn_df['Start'].apply(lambda times: sorted(times, key=lambda x: int(x.split(':')[0])))
        
        # Arrange order 'LOW-MODERATE-HIGH'
        current_stn_df['CrowdVolume'] = pd.Categorical(current_stn_df['CrowdVolume'], categories=['LOW', 'MODERATE', 'HIGH'], ordered=True)
        current_stn_df = current_stn_df.sort_values('CrowdVolume')
        
        all_volume_df = pd.concat([all_volume_df, current_stn_df])
    
    all_volume_df.reset_index(drop=True, inplace=True)
    all_volume_df = get_station_names(all_volume_df, None)
    
    time_string = summarize_volume_time(all_volume_df)
    return time_string


def clean_volume(data_df, prompt_df, date_time):
    """
    Filter volume data by time and station.
    
    Args:
        data_df (DataFrame): DataFrame containing volume data
        prompt_df (DataFrame): DataFrame containing station data
        date_time (str): Date and time string
        
    Returns:
        str: Summary of volume data
    """
    from utils.time_utils import split_date_time
    from utils.transport_utils import summarize_crowd, get_station_names
    from config.settings import PASSENGER_UPPER_THRESHOLD, PASSENGER_LOWER_THRESHOLD
    
    # Clean date
    day, time = split_date_time(date_time)
    time_hr = time.hour
    
    selected_list = []
    
    # Filtering through DataFrame
    filtered_df = pd.DataFrame()
    
    for stn_code in prompt_df['stn_codes'].unique():
        filtered_df = pd.concat([filtered_df, data_df[data_df['PT_CODE'] == stn_code]])
    
    for _, row in filtered_df.iterrows():
        if row['DAY_TYPE'] == day and row['TIME_PER_HOUR'] == time_hr:
            selected_list.append(row)
    
    if not selected_list:
        return "No volume data available for the selected time and stations."
    
    # Check crowd volume
    selected_list_df = pd.DataFrame(selected_list)
    selected_list_df = selected_list_df.reset_index(drop=True)
    
    passenger_volume = selected_list_df.loc[0, 'TOTAL_TAP_IN_VOLUME'] + selected_list_df.loc[0, 'TOTAL_TAP_OUT_VOLUME']
    
    selected_list_df.insert(1, 'CrowdLevel', 
                          'CROWD LEVEL HIGH' if passenger_volume > PASSENGER_UPPER_THRESHOLD 
                          else ('CROWD LEVEL LOW' if passenger_volume < PASSENGER_LOWER_THRESHOLD 
                              else 'CROWD LEVEL MODERATE'))
    
    selected_list_df = selected_list_df.loc[:, ['PT_CODE', 'CrowdLevel']]
    selected_list_df.rename(columns={'PT_CODE': 'Station'}, inplace=True)
    
    selected_list_df = get_station_names(selected_list_df, None)
    selected_list_string = summarize_crowd(selected_list_df)
    
    return selected_list_string


def clean_to_fro_volume(data_df, start_stn, end_stn, date_time):
    """
    Filter origin-destination volume data.
    
    Args:
        data_df (DataFrame): DataFrame containing volume data
        start_stn (str): Start station code
        end_stn (str): End station code
        date_time (str): Date and time string
        
    Returns:
        str: Summary of volume data between stations
    """
    from utils.time_utils import split_date_time
    from utils.transport_utils import get_station_names
    from config.settings import PASSENGER_UPPER_THRESHOLD, PASSENGER_LOWER_THRESHOLD
    
    # Clean date
    day, time = split_date_time(date_time)
    time_hr = time.hour
    
    passenger_upper_threshold = 57   # 75% 
    passenger_lower_threshold = 4    # 25%
    
    selected_list = []
    
    # Filtering through DataFrame
    data_df = data_df[data_df['ORIGIN_PT_CODE'].str.contains(start_stn)]
    data_df = data_df[data_df['DESTINATION_PT_CODE'].str.contains(end_stn)]
    
    # Process origin station
    data_df.rename(columns={'ORIGIN_PT_CODE': 'PT_CODE'}, inplace=True)
    origin_df = clean_csv(data_df, 'ORIGIN')
    
    # Process destination station
    data_df.rename(columns={'DESTINATION_PT_CODE': 'PT_CODE'}, inplace=True)
    dest_df = clean_csv(data_df, 'DESTINATION')
    
    # Filter by exact station codes
    filtered_df = origin_df[origin_df['ORIGIN_PT_CODE'] == start_stn]
    filtered_df = filtered_df[filtered_df['DESTINATION_PT_CODE'] == end_stn]
    
    for _, row in filtered_df.iterrows():
        if row['DAY_TYPE'] == day and row['TIME_PER_HOUR'] == time_hr:
            selected_list.append(row)
            break
    
    if not selected_list:
        return "No volume data available for the selected stations and time."
    
    # Check crowd volume 
    selected_list_df = pd.DataFrame(selected_list).loc[:, ['ORIGIN_PT_CODE', 'DESTINATION_PT_CODE', 'TOTAL_TRIPS']]
    selected_list_df = selected_list_df.reset_index(drop=True)
    
    passenger_volume = selected_list_df.loc[0, 'TOTAL_TRIPS']
    
    selected_list_df.insert(1, 'CrowdLevel', 
                          'CROWD LEVEL HIGH' if passenger_volume > passenger_upper_threshold 
                          else ('CROWD LEVEL LOW' if passenger_volume < passenger_lower_threshold 
                              else 'CROWD LEVEL MODERATE'))
    
    selected_list_df = selected_list_df.loc[:, ['CrowdLevel', 'ORIGIN_PT_CODE', 'DESTINATION_PT_CODE']]
    
    # Add station names
    selected_list_df.rename(columns={'ORIGIN_PT_CODE': 'Station'}, inplace=True)
    selected_list_df = get_station_names(selected_list_df, 'ORIGIN')
    
    selected_list_df.rename(columns={'DESTINATION_PT_CODE': 'Station'}, inplace=True)
    selected_list_df = get_station_names(selected_list_df, 'DESTINATION')
    
    # Format output
    selected_list_df.insert(1, 'from', 'from')
    selected_list_df.insert(3, 'to', 'to')
    selected_list_df.insert(5, '.', '.')
    
    return selected_list_df.to_string(index=False, header=False)


def clean_csv(df, where=None):
    """
    Clean CSV data by splitting station codes with '/' character.
    
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