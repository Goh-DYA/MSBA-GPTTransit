"""
LangChain tools for transport-related operations.
"""

import pandas as pd
import re
from typing import Optional

from langchain.agents import tool
from config.settings import MRT_LRT_DATA_PATH
from api.onemap_api import get_public_transport_route
from utils.time_utils import clean_time_prompt
from utils.transport_utils import (
    clean_station_prompt, 
    clean_alert_prompt,
    summarize_alerts,
    get_station_names
)
from api.lta_api import (
    get_data_request, 
    get_service_status,
    validate_station_alert
)


@tool
def get_public_transport_route_concise(station: str) -> str:
    """
    Get the journey time, cost and list of train stations from one MRT train station to another MRT train station.
    Also, find walking routes and number of steps between MRT train stations.
    
    Args:
        station (str): Input in format 'start_station,end_station'
        
    Returns:
        str: Details of possible routes
    """
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(MRT_LRT_DATA_PATH)
        start_station, end_station = str(station).split(",")
        start_station = start_station.upper().replace(" ", "")  # updated so that all spaces will become blank
        end_station = end_station.upper().replace(" ", "")  # updated so that all spaces will become blank

        # Get starting station details
        station_start = df[df['station_name'] == start_station]
        if station_start.empty:
            start_not_found = f"Starting station '{start_station}' not found, do ensure that the spelling is correct."
            return start_not_found
        lat_start = station_start['lat'].values[0]
        lng_start = station_start['lng'].values[0]

        # Get destination station details
        station_end = df[df['station_name'] == end_station]
        if station_end.empty:
            dest_not_found = f"Destination station '{end_station}' not found, do ensure that the spelling is correct."
            return dest_not_found
        lat_end = station_end['lat'].values[0]
        lng_end = station_end['lng'].values[0]
        code_end = station_end['station_code'].values[0]  # get destination station code for walk as last leg
        name_end = station_end['full_name'].values[0]  # get destination station name for walk as last leg

        # Get route information from OneMap API
        api_response = get_public_transport_route((lat_start, lng_start), (lat_end, lng_end))
        
        if not api_response:
            return "The API request failed, please try again later."
        
        # Extract route information from API response
        routes_str = ""
        route_count = 1
        api_response_itineraries = api_response['plan']['itineraries']
        walk_legs = 0

        for itinerary in api_response_itineraries:
            for leg in itinerary['legs']:
                if leg['mode'] == 'WALK' and leg['from']['name'] == 'Origin' and leg['to']['name'] == 'Destination':
                    walk_legs += 1

        routes_count = len(api_response_itineraries) - walk_legs
        routes_str += f"There are {routes_count} possible travel route(s).\n"

        for itinerary in api_response_itineraries:  # pull out all the itineraries or routes from the api
            route_string = ""
            duration = itinerary['duration'] / 60  # calculate overall duration of the route
            fare = itinerary['fare']  # extract total fare of the route
            prev_station_name = None
            first_leg = itinerary['legs'][0]  # Extracting the first leg
            last_leg = itinerary['legs'][-1]  # Extracting the last leg
            transit_distance = 0

            if first_leg['mode'] == 'WALK' and \
                first_leg['from']['name'] == 'Origin' and \
                first_leg['to']['name'].replace(' MRT STATION', '').replace(' ', '') != start_station and \
                first_leg['to']['name'] != 'Destination':

                route_string += f"Walk {round(first_leg['distance'],0)} metres or {round(first_leg['distance']/0.75,0)} steps to {first_leg['to']['stopCode']} {first_leg['to']['name'].replace(' MRT STATION', '')} "

            for leg_index, leg in enumerate(itinerary['legs']):  # within each itinerary, look for each leg of the route
                
                if leg_index > 0 and leg_index < len(itinerary['legs']) - 1 and \
                    leg['mode'] == 'WALK' and \
                    leg['from']['name'] != leg['to']['name']:  # to include "walk leg from one station to another" in the route string
                    route_string += f" then walk {round(leg['distance'],0)} metres or {round(leg['distance']/0.75,0)} steps"  

                if leg_index > 0 and leg_index < len(itinerary['legs']) - 1 and \
                    leg['mode'] == 'WALK' and \
                    leg['from']['name'] == leg['to']['name']:  # to include "walk leg for transit" 
                    transit_distance = leg['distance']  

                if leg_index > 0 and leg_index < len(itinerary['legs']) - 1 and \
                    leg['mode'] == 'SUBWAY' and \
                    leg['from']['name'] == leg['to']['name']:  # to include "walk leg for transit cross platform only" 
                    transit_distance = 0
                    
                if leg['mode'] == 'SUBWAY':  # if the leg is a subway route

                    if route_string.startswith("Walk"):  # Check if route_string starts with "Walk"
                        route_string += "then take train from "
                    elif route_string:
                        route_string += " to "
                    current_station_name = leg['from']['name'].replace(' MRT STATION', '')  # remove excess words

                    if current_station_name == prev_station_name and transit_distance != 0:
                        route_string += f"transit by walking {round(transit_distance,0)} metres or {round(transit_distance/0.75,0)} steps to "  # include the walking to transit station
                    elif current_station_name == prev_station_name and transit_distance == 0:
                        route_string += f"transit by crossing the platform (10 meters, 13 steps) to "  # include the walking to transit station
                                        
                    route_string += f"{leg['from']['stopCode']} {current_station_name}"
                    prev_station_name = leg['to']['name'].replace(' MRT STATION', '')  # remove excess words
                    route_string += f" to {leg['to']['stopCode']} {prev_station_name}"

            # Check if the last leg is a 'WALK' mode and meets the conditions
            if last_leg['mode'] == 'WALK' and \
                last_leg['to']['name'] == 'Destination' and \
                last_leg['from']['name'].replace(' MRT STATION', '').replace(' ', '') != end_station and \
                last_leg['from']['name'] != 'Origin':
                if route_string:  # If route_string is not empty, add "Walk to end station"
                    routes_str += f"Route {route_count}: {route_string} then walk {round(last_leg['distance'],0)} metres or {round(last_leg['distance']/0.75,0)} steps to {code_end} {name_end} with an estimated duration of {round(duration, 0)} minutes and cost ${fare}.\n"
            elif route_string:  # Check if route_string is not empty before adding to routes_str
                routes_str += f"Route {route_count}: {route_string} with an estimated duration of {round(duration, 0)} minutes and cost ${fare}.\n"
            
            # Increment the route count at the end of the loop
            route_count += 1
                                  
        return routes_str

    except Exception as e:
        exception_msg = f"An error occurred: {str(e)}"
        return exception_msg


@tool
def checkTrainAlert(input_prompt: str) -> str:
    """
    Check for any disruptions or unavailability of train services.
    
    Args:
        input_prompt (str): Input in format 'station_name' OR 'start_station,end_station'
        
    Returns:
        str: Details of any train service alerts
    """
    # Clean prompt
    text_input_prompt, _ = clean_time_prompt(input_prompt)
    
    # Get route information
    stations_info = get_public_transport_route_concise(text_input_prompt)
    
    if "Error" not in stations_info:
        prompt_stn_df, _, _ = clean_station_prompt(stations_info)

        # Get service alerts data
        url_type = 'alert'
        response = get_data_request(url_type)
        
        if response is not None:
            # Check service status
            if response['value']['Status'] == 1:
                return "There are no real-time train service issues at the selected stations."
            else:
                # Process alert data
                status_list = []
                message = get_service_status(response)
                
                for code in (prompt_stn_df['stn_codes']):
                    status_list.append(validate_station_alert(message, code))

                # Summarize alerts
                status_df = pd.DataFrame({
                    'Station': prompt_stn_df['stn_codes'],
                    'Status': status_list
                })
                
                status_df = get_station_names(status_df, None)
                status_string = summarize_alerts(status_df)
                
                return status_string
        else:
            return "Error: The API call was unsuccessful. Please try again later."
    else:
        return "Error: No routes available. Please try again later."