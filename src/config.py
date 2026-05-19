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
