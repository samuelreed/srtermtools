#!/usr/bin/env python3

"""
AQI Checker - Monitor air quality index from AirNow API

Usage:
    aqicheck.py [<zipcode>] [--MOD|--USG|--UH|--VUH|--HAZ]

Options:
    --MOD    Show if AQI is Moderate or worse (≥51)
    --USG    Show if Unhealthy for Sensitive Groups or worse (≥101)  
    --UH     Show if Unhealthy or worse (≥151)
    --VUH    Show if Very Unhealthy or worse (≥201)
    --HAZ    Show if Hazardous (≥301)

Examples:
    aqicheck.py 94105 --USG
    aqicheck.py --MOD

Configuration:
    Requires ~/.aqi.ini file with:
    [DEFAULT]
    api_key = your_airnow_api_key
    zipcode = your_default_zipcode
"""

from pathlib import Path
from docopt import docopt
from termcolor import colored
from typing import Dict, Optional, Tuple
import os
import sys
import requests
import requests_cache
import configparser

# Constants
AQI_API = "http://www.airnowapi.org/aq/observation/zipCode/current/"
CROSS_MARK = "✗"
CHECK_MARK = "✓"

# AQI threshold mappings
AQI_THRESHOLDS = {
    'MOD': 2,    # Moderate
    'USG': 3,    # Unhealthy for Sensitive Groups  
    'UH': 4,     # Unhealthy
    'VUH': 5,    # Very Unhealthy
    'HAZ': 6     # Hazardous
}

# AQI color ranges: (max_value, color)
AQI_COLOR_RANGES = [
    (50, "green"),      # Good (0-50)
    (100, "yellow"),    # Moderate (51-100)
    (150, "yellow"),    # Unhealthy for Sensitive Groups (101-150)
    (200, "red"),       # Unhealthy (151-200)
    (300, "magenta"),   # Very Unhealthy (201-300)
    (float('inf'), "magenta")  # Hazardous (301+)
]

# File permissions
SECURE_FILE_MODE = 0o600

proxies = {}
# proxies = {'http': 'http://localhost:9191', 'https': 'http://localhost:9191'}


def get_aqi_color(value: int) -> str:
    """Return color for the AQI range using data-driven approach."""
    for max_value, color in AQI_COLOR_RANGES:
        if value <= max_value:
            return color
    return "blue"  # fallback color


def load_configuration() -> Tuple[str, str]:
    """Load and validate configuration from ~/.aqi.ini file."""
    config_path = Path.home() / ".aqi.ini"
    
    # Check if config file exists
    if not config_path.exists():
        print(f"[{colored(CROSS_MARK, 'red')}] Configuration file {config_path} not found.")
        print("Create ~/.aqi.ini with:")
        print("[DEFAULT]")
        print("api_key = your_airnow_api_key")
        print("zipcode = your_default_zipcode")
        sys.exit(1)
    
    # Check file permissions
    if oct(config_path.stat().st_mode & 0o777) != "0o600":
        print(f"[{colored(CROSS_MARK, 'red')}] Fix file permissions on .aqi.ini file to 600.")
        sys.exit(1)
    
    # Load and validate configuration
    config_parser = configparser.ConfigParser()
    try:
        config_parser.read(config_path)
    except configparser.Error as e:
        print(f"[{colored(CROSS_MARK, 'red')}] Error reading config file: {e}")
        sys.exit(1)
    
    # Validate required keys
    required_keys = ["api_key", "zipcode"]
    for key in required_keys:
        if key not in config_parser["DEFAULT"] or not config_parser["DEFAULT"][key].strip():
            print(f"[{colored(CROSS_MARK, 'red')}] Missing or empty '{key}' in config file")
            sys.exit(1)
    
    api_key = config_parser["DEFAULT"]["api_key"].strip()
    default_zipcode = config_parser["DEFAULT"]["zipcode"].strip()
    
    return api_key, default_zipcode


def get_aqi_threshold(args: Dict) -> int:
    """Get AQI threshold based on command line arguments."""
    for flag, threshold in AQI_THRESHOLDS.items():
        if args[f"--{flag}"]:
            return threshold
    return 0  # Default: show all AQI levels


def setup_cache() -> None:
    """Setup request cache with proper file permissions."""
    cache_path = Path.home() / ".dirty-aqi-cache"
    requests_cache.install_cache(str(cache_path), expire_after=3600)
    
    # Ensure cache file has secure permissions
    sqlite_cache = cache_path.with_suffix(".sqlite")
    if sqlite_cache.exists():
        if oct(sqlite_cache.stat().st_mode & 0o777) != "0o600":
            os.chmod(sqlite_cache, SECURE_FILE_MODE)


def process_aqi_data(response_data: list, zipcode: str, threshold: int) -> None:
    """Process and display AQI data from API response."""
    pm25_data = None
    
    # Find PM2.5 data
    for measurement in response_data:
        if measurement["ParameterName"] == "PM2.5":
            pm25_data = measurement
            break
    
    if not pm25_data:
        print(f"[{colored(CROSS_MARK, 'red')}] No PM2.5 data available for zipcode {zipcode}")
        sys.exit(1)
    
    # Check if AQI meets threshold
    if pm25_data["Category"]["Number"] >= threshold:
        aqi_color = get_aqi_color(pm25_data["AQI"])
        message = (
            f"[{colored(pm25_data['AQI'], aqi_color)}] "
            f"AirNow reports AQI for {zipcode} is "
            f"{colored(pm25_data['Category']['Name'], aqi_color)} "
            f"as of {pm25_data['HourObserved']}:00 {pm25_data['LocalTimeZone']}."
        )
        print(message)


if __name__ == "__main__":
    args = docopt(__doc__, version="0.1")

    # Load configuration and setup
    api_key, default_zipcode = load_configuration()
    
    # Determine zipcode to use
    zipcode = args["<zipcode>"] if args["<zipcode>"] is not None else default_zipcode
    
    # Setup caching
    setup_cache()
    
    # Get AQI threshold
    aqi_threshold = get_aqi_threshold(args)

    # Prepare API request
    payload = {
        "format": "application/json",
        "distance": "5",
        "zipCode": zipcode,
        "API_KEY": api_key,
    }

    try:
        response = requests.get(AQI_API, params=payload, proxies=proxies)
        if response.status_code != 200:
            print(f"[{colored(CROSS_MARK, 'red')}] API request failed with status {response.status_code}: {response.reason}")
            sys.exit(1)

        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"[{colored(CROSS_MARK, 'red')}] Invalid JSON response from API")
            sys.exit(1)
        
        # Process and display AQI data
        process_aqi_data(response_data, zipcode, aqi_threshold)
        
    except requests.exceptions.RequestException as err:
        print(f"[{colored(CROSS_MARK, 'red')}] RequestException: {err} (common when disconnected from Internet)")
        sys.exit(1)
