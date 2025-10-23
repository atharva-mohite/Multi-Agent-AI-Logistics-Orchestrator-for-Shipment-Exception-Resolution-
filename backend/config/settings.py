"""Configuration settings for Maritime Exception Resolution System"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# Bedrock Configuration
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
BEDROCK_GUARDRAIL_ID = os.getenv("BEDROCK_GUARDRAIL_ID")
BEDROCK_GUARDRAIL_VERSION = os.getenv("BEDROCK_GUARDRAIL_VERSION", "1")

# Application Settings
APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")

# Data Files
WAYPOINT_GRID_FILE = DATA_DIR / "maritime_waypoint_grid.csv"
ROUTES_FILE = DATA_DIR / "port_to_port_routes.csv"
CARRIER_SCHEDULE_FILE = DATA_DIR / "Table1_Carrier_Route_Schedule.csv"
PORT_LOCATIONS_FILE = DATA_DIR / "Table2_Master_Port_Locations.csv"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# Telemetry
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
ENABLE_TRACING = os.getenv("ENABLE_TRACING", "true").lower() == "false"

# Security Settings
ENABLE_PII_REDACTION = os.getenv("ENABLE_PII_REDACTION", "true").lower() == "true"
ENABLE_PROFANITY_SCAN = os.getenv("ENABLE_PROFANITY_SCAN", "true").lower() == "true"
ENABLE_GUARDRAILS = os.getenv("ENABLE_GUARDRAILS", "true").lower() == "false"


# Create a settings object for easier import
class Settings:
    """Settings object for easy access"""
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
    AWS_DEFAULT_REGION = AWS_DEFAULT_REGION
    BEDROCK_MODEL_ID = BEDROCK_MODEL_ID
    BEDROCK_GUARDRAIL_ID = BEDROCK_GUARDRAIL_ID
    BEDROCK_GUARDRAIL_VERSION = BEDROCK_GUARDRAIL_VERSION
    APP_DEBUG = APP_DEBUG
    APP_PORT = APP_PORT
    APP_HOST = APP_HOST
    WAYPOINT_GRID_FILE = WAYPOINT_GRID_FILE
    ROUTES_FILE = ROUTES_FILE
    CARRIER_SCHEDULE_FILE = CARRIER_SCHEDULE_FILE
    PORT_LOCATIONS_FILE = PORT_LOCATIONS_FILE
    LOG_LEVEL = LOG_LEVEL
    LOG_FORMAT = LOG_FORMAT
    OTEL_ENDPOINT = OTEL_ENDPOINT
    ENABLE_TRACING = ENABLE_TRACING
    ENABLE_PII_REDACTION = ENABLE_PII_REDACTION
    ENABLE_PROFANITY_SCAN = ENABLE_PROFANITY_SCAN
    ENABLE_GUARDRAILS = ENABLE_GUARDRAILS


settings = Settings()