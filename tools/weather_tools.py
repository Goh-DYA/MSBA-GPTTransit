"""
LangChain tools for weather-related operations.
"""

from langchain.agents import tool
from utils.weather_utils import get_combined_weather_forecast


@tool
def get_2h_24h_weather_forecast(passthrough: str) -> str:
    """
    Get the weather forecast for the next 2 and 24 hours.
    
    Args:
        passthrough (str): Any string (not used)
        
    Returns:
        str: Combined weather forecast
    """
    return get_combined_weather_forecast()