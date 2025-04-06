"""
Configuration settings for the GPTTransit application.
Loads environment variables and sets up configuration parameters.
"""

import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
_ = load_dotenv(find_dotenv())

# API Keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
LTA_API_KEY = os.environ.get("LTA_API_KEY")
ONEMAP_API_KEY = os.environ.get("ONEMAP_API_KEY")

# Model configurations
OPENAI_MODEL = "gpt-4o-mini" #"gpt-4-turbo"
MISTRAL_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
TEMPERATURE_OPENAI = 0  # Set temperature to 0 for deterministic outputs
TEMPERATURE_HF = 0.01  # Set temperature to 0.01 for HuggingFace models

# Data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MRT_LRT_DATA_PATH = os.path.join(DATA_DIR, "mrtlrt_gps.csv")
TAXI_STANDS_DATA_PATH = os.path.join(DATA_DIR, "taxi_stands_Monthly.csv")
TRANSPORT_NODE_DATA_PATH = os.path.join(DATA_DIR, "transport_node_train_202402.csv")

# API URLs
LTA_BASE_URL = "http://datamall2.mytransport.sg/ltaodataservice"
ONEMAP_BASE_URL = "https://www.onemap.gov.sg/api"

# Default parameters
MAX_WALK_DISTANCE = 100
NUM_ITINERARIES = 3
PASSENGER_UPPER_THRESHOLD = 95000  # threshold between "medium-to-high"
PASSENGER_LOWER_THRESHOLD = 15000  # threshold between "low-to-medium"