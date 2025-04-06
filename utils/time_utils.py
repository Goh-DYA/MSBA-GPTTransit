"""
Utility functions for handling time and date operations.
"""

from datetime import datetime, timedelta


def clean_time_prompt(prompt):
    """
    Split a prompt into station information and date/time.
    
    Args:
        prompt (str): User input prompt
        
    Returns:
        tuple: (station_info, date_time)
    """
    # Segregate 'start_stn, end_stn; time'
    parts = prompt.split(';')
    text = parts[0].strip()
    
    # Check time info
    date_time = parts[1].strip() if len(parts) > 1 and parts[1].strip() else ","
    
    return text, date_time


def split_date_time(prompt):
    """
    Split date and time information from input.
    
    Args:
        prompt (str): Date/time string
        
    Returns:
        tuple: (day_type, time_object)
    """
    if ',' in prompt:
        date_str, time_str = prompt.split(',', 1)
        # If both empty: get current date & time
        date = datetime.now().strftime("%d-%m-%Y") if not date_str.strip() else date_str.strip()
        
        if not time_str.strip():
            time = datetime.now().strftime("%H:%M")
        else:
            # Check if time is in 'HHMM' format
            time_input = time_str.strip()
            if len(time_input) == 4 and time_input.isdigit():
                time = time_input[:2] + ":" + time_input[2:]
            else:
                time = time_input
    else:
        if len(prompt) == 0:
            date = datetime.now().strftime("%d-%m-%Y")
            time = datetime.now().strftime("%H:%M")
        else:
            if len(prompt) <= 5:
                date = datetime.now().strftime("%d-%m-%Y")
                if not prompt.strip():
                    time = datetime.now().strftime("%H:%M")
                else:
                    # Check if time is in 'HHMM' format
                    time_input = prompt.strip()
                    if len(time_input) == 4 and time_input.isdigit():
                        time = time_input[:2] + ":" + time_input[2:]
                    else:
                        time = time_input
            else:
                date = prompt
                time = datetime.now().strftime("%H:%M")
    
    # Check weekday/weekend
    day = 'WEEKDAY' if datetime.strptime(date, "%d-%m-%Y").weekday() < 5 else 'WEEKENDS/HOLIDAY'
    
    time_obj = datetime.strptime(time, "%H:%M")
    
    return day, time_obj


def get_rounded_time(time_delta_minutes=0):
    """
    Get current time with optional offset, rounded to nearest 30 mins.
    
    Args:
        time_delta_minutes (int): Minutes to add to current time
        
    Returns:
        datetime: Rounded time
    """
    now = datetime.now() + timedelta(minutes=time_delta_minutes)
    
    # Round to nearest 30 mins
    rounded_minutes = (now.minute // 30) * 30
    
    if rounded_minutes == 0:
        now = now.replace(minute=0)
    else:
        now = now.replace(minute=rounded_minutes)
    
    return now


def check_weekday_or_weekend(date_time_string):
    """
    Check if a given date is a weekday or weekend.
    
    Args:
        date_time_string (str): Date time string in format "DD-MM-YYYY,HH:MM"
        
    Returns:
        str: Message indicating if the date is a weekday or weekend
    """
    # Convert date/time string to datetime object
    date_time_obj = datetime.strptime(date_time_string, '%d-%m-%Y,%H:%M')
    
    # Extract the weekday number (0: Monday, 1: Tuesday, ..., 6: Sunday)
    weekday_num = date_time_obj.weekday()
    
    # Check if it's a weekday (Monday to Friday)
    if weekday_num < 5:
        return f"{date_time_obj.strftime('%d-%m-%Y')} is a WEEKDAY.\n"
    else:
        return f"{date_time_obj.strftime('%d-%m-%Y')} is a WEEKEND.\n"