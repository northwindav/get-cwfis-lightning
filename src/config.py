# Loads credentials from the .env file

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('HOST'),
    'user': os.getenv('USER'),
    'database': os.getenv('DATABASE'),
    'table': os.getenv('TABLE'),
    'password': os.getenv('PASSWORD', None),
}

# Validate that required fields are present
required_fields = ['host', 'user', 'database', 'table']
for field in required_fields:
    if not DB_CONFIG[field]:
        raise ValueError(f"Missing required environment variable: {field.upper()}")

# Output directory configuration
OUTPUT_DIR = {
    'tmp': Path(__file__).parent.parent / 'tmp',
    'images': Path(__file__).parent.parent / 'images',
}

# Ensure output directories exist
for dir_path in OUTPUT_DIR.values():
    dir_path.mkdir(exist_ok=True)

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Predefined bounding box regions for map visualization
# Each region includes: min_lon, min_lat, max_lon, max_lat (WGS84) and crs (projection code)
# Note that a change in EPSG may require changing default bounding coordinates as well. 
REGION_BOUNDS = {
    'yukon': {'min_lon': -142, 'min_lat': 59, 'max_lon': -124, 'max_lat': 70, 'crs': 'EPSG:3578'},  # NAD83 Yukon Albers
    'british-columbia': {'min_lon': -139, 'min_lat': 48.0, 'max_lon': -114, 'max_lat': 60, 'crs': 'EPSG:3153'},
    'bc': {'min_lon': -139, 'min_lat': 48.0, 'max_lon': -114, 'max_lat': 60, 'crs': 'EPSG:3153'},
    'alberta': {'min_lon': -120, 'min_lat': 48.5, 'max_lon': -109.5, 'max_lat': 60.5, 'crs': 'EPSG:3403'},
    'ab': {'min_lon': -120, 'min_lat': 48.5, 'max_lon': -109.5, 'max_lat': 60.5, 'crs': 'EPSG:3403'},
    'northwest-territories': {'min_lon': -141, 'min_lat': 58, 'max_lon': -102, 'max_lat': 70, 'crs': 'EPSG:3581'},  # NAD83 / NWT Lambert
    'nwt': {'min_lon': -141, 'min_lat': 58, 'max_lon': -102, 'max_lat': 70, 'crs': 'EPSG:3581'},
    'saskatchewan': {'min_lon': -110, 'min_lat': 48.5, 'max_lon': -102, 'max_lat': 60.5, 'crs': 'EPSG:2957'},
    'sk': {'min_lon': -110, 'min_lat': 48.5, 'max_lon': -102, 'max_lat': 60.5, 'crs': 'EPSG:2957'},
    'manitoba': {'min_lon': -102, 'min_lat': 49, 'max_lon': -95, 'max_lat': 60, 'crs': 'EPSG:3978'},
    'mb': {'min_lon': -102, 'min_lat': 49, 'max_lon': -95, 'max_lat': 60, 'crs': 'EPSG:3978'},
    'ontario': {'min_lon': -95, 'min_lat': 41, 'max_lon': -74, 'max_lat': 56, 'crs': 'EPSG:3978'},
    'on': {'min_lon': -95, 'min_lat': 41, 'max_lon': -74, 'max_lat': 56, 'crs': 'EPSG:3978'},
    'quebec': {'min_lon': -79, 'min_lat': 45, 'max_lon': -57, 'max_lat': 55, 'crs': 'EPSG:3978'},
    'qc': {'min_lon': -79, 'min_lat': 45, 'max_lon': -57, 'max_lat': 55, 'crs': 'EPSG:3978'},
    'atlantic': {'min_lon': -67, 'min_lat': 43, 'max_lon': -52, 'max_lat': 48, 'crs': 'EPSG:3978'},
    'atlantic-canada': {'min_lon': -67, 'min_lat': 43, 'max_lon': -52, 'max_lat': 48, 'crs': 'EPSG:3978'},
    'western-canada': {'min_lon': -141, 'min_lat': 49, 'max_lon': -110, 'max_lat': 70, 'crs': 'EPSG:3978'},
    'prairies': {'min_lon': -120, 'min_lat': 49, 'max_lon': -95, 'max_lat': 60, 'crs': 'EPSG:3978'},
}

def get_region_bounds(region_name: str) -> dict:
    """Get bounding box coordinates for a named region."""
    region_lower = region_name.lower()
    if region_lower not in REGION_BOUNDS:
        available = ', '.join(sorted(set(k for k in REGION_BOUNDS.keys() if len(k) < 20)))
        raise ValueError(f"Unknown region: '{region_name}'. Available: {available}")
    return REGION_BOUNDS[region_lower]
