"""
Utility functions for fetching and processing weather data.
"""

import requests
from collections import Counter


def get_2h_weather_forecast():
    """
    Get the nationwide aggregated weather forecast for the next 2 hours.
    
    Returns:
        str: Weather forecast for the next 2 hours
    """
    try:
        url = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()

            # Extract forecasts
            forecasts = data["items"][0]["forecasts"]

            # Count the occurrences of each forecast
            forecast_counter = Counter([forecast["forecast"] for forecast in forecasts])

            # Get the most common forecast
            forecast_2hrs = forecast_counter.most_common(1)[0][0]
            return forecast_2hrs
        else:
            return f"Error: Unable to fetch 2-hour weather forecast data (status code: {response.status_code})."
    except Exception as e:
        return f"Error: {e}"


def get_24h_weather_forecast():
    """
    Get the nationwide weather forecast for the next 24 hours.
    
    Returns:
        str: Weather forecast for the next 24 hours
    """
    try:
        url = "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast"
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()

            # Extract forecast from the "general" key
            forecast_24hrs = data["items"][0]["general"]["forecast"]
            return forecast_24hrs
        else:
            return f"Error: Unable to fetch 24-hour weather forecast data (status code: {response.status_code})."
    except Exception as e:
        return f"Error: {e}"


def get_combined_weather_forecast():
    """
    Get combined 2-hour and 24-hour weather forecasts.
    
    Returns:
        str: Combined weather forecast message
    """
    forecast_2h = get_2h_weather_forecast()
    forecast_24h = get_24h_weather_forecast()

    # Check for errors. If yes, highlight that the forecast is not available.
    if "Error" in forecast_2h:
        forecast_2h = f"Not available due to '{forecast_2h}'"
    if "Error" in forecast_24h:
        forecast_24h = f"Not available due to '{forecast_24h}'"
    
    # Construct weather forecast message
    forecast_message = f"2-Hour weather forecast: {forecast_2h}.\n24-Hour weather forecast: {forecast_24h}."

    return forecast_message