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

import configparser
import os
import sys
from pathlib import Path
from typing import Any, Dict, NoReturn, Optional, Tuple, cast

import requests
import requests_cache
from docopt import DocoptExit, docopt
from termcolor import colored

# Constants
AQI_API = "http://www.airnowapi.org/aq/observation/zipCode/current/"
CROSS_MARK = "✗"
CHECK_MARK = "✓"

# AQI threshold mappings
AQI_THRESHOLDS = {
    "MOD": 2,  # Moderate
    "USG": 3,  # Unhealthy for Sensitive Groups
    "UH": 4,  # Unhealthy
    "VUH": 5,  # Very Unhealthy
    "HAZ": 6,  # Hazardous
}

# AQI color ranges: (max_value, color)
AQI_COLOR_RANGES = [
    (50, "green"),  # Good (0-50)
    (100, "yellow"),  # Moderate (51-100)
    (150, "yellow"),  # Unhealthy for Sensitive Groups (101-150)
    (200, "red"),  # Unhealthy (151-200)
    (300, "magenta"),  # Very Unhealthy (201-300)
    (float("inf"), "magenta"),  # Hazardous (301+)
]

# File permissions
SECURE_FILE_MODE = 0o600

proxies: Dict[str, str] = {}
# proxies = {'http': 'http://localhost:9191', 'https': 'http://localhost:9191'}


def get_aqi_color(value: int) -> str:
    """Return color for the AQI range using data-driven approach."""
    for max_value, color in AQI_COLOR_RANGES:
        if value <= max_value:
            return color
    return "blue"  # fallback color


def print_error(message: str) -> None:
    print(f"[{colored(CROSS_MARK, 'red')}] {message}", file=sys.stderr)


def fail(message: str) -> NoReturn:
    print_error(message)
    raise SystemExit(1)


def load_configuration(config_path: Optional[Path] = None) -> Tuple[str, str]:
    """Load and validate configuration from ~/.aqi.ini file."""
    if config_path is None:
        config_path = Path.home() / ".aqi.ini"

    if not config_path.exists():
        print_error(f"Configuration file {config_path} not found.")
        print("Create ~/.aqi.ini with:", file=sys.stderr)
        print("[DEFAULT]", file=sys.stderr)
        print("api_key = your_airnow_api_key", file=sys.stderr)
        print("zipcode = your_default_zipcode", file=sys.stderr)
        sys.exit(1)

    if config_path.stat().st_mode & 0o777 != SECURE_FILE_MODE:
        fail(f"Fix file permissions on .aqi.ini file to {SECURE_FILE_MODE:o}.")

    config_parser = configparser.ConfigParser()
    try:
        config_parser.read(config_path)
    except configparser.Error as e:
        fail(f"Error reading config file: {e}")

    required_keys = ["api_key", "zipcode"]
    for key in required_keys:
        if (
            key not in config_parser["DEFAULT"]
            or not config_parser["DEFAULT"][key].strip()
        ):
            fail(f"Missing or empty '{key}' in config file")

    api_key = config_parser["DEFAULT"]["api_key"].strip()
    default_zipcode = config_parser["DEFAULT"]["zipcode"].strip()

    return api_key, default_zipcode


def get_aqi_threshold(args: Dict) -> int:
    """Get AQI threshold based on command line arguments."""
    for flag, threshold in AQI_THRESHOLDS.items():
        if args[f"--{flag}"]:
            return threshold
    return 0  # Default: show all AQI levels


def setup_cache(cache_path: Optional[Path] = None) -> None:
    """Setup request cache with proper file permissions."""
    if cache_path is None:
        cache_path = Path.home() / ".dirty-aqi-cache"
    requests_cache.install_cache(str(cache_path), expire_after=3600)

    sqlite_cache = cache_path.with_suffix(".sqlite")
    if sqlite_cache.exists():
        if sqlite_cache.stat().st_mode & 0o777 != SECURE_FILE_MODE:
            os.chmod(sqlite_cache, SECURE_FILE_MODE)


def process_aqi_data(
    response_data: list, zipcode: str, threshold: int
) -> None:
    """Process and display AQI data from API response."""
    if not isinstance(response_data, list):
        fail(f"Unexpected AQI response format for zipcode {zipcode}")

    pm25_data = None

    for measurement in response_data:
        if not isinstance(measurement, dict):
            continue
        if measurement.get("ParameterName") == "PM2.5":
            pm25_data = measurement
            break

    if not pm25_data:
        fail(f"No PM2.5 data available for zipcode {zipcode}")

    pm25_details = cast(Dict[str, Any], pm25_data)
    try:
        category = cast(Dict[str, Any], pm25_details["Category"])
        category_number = int(category["Number"])
        aqi_value = int(pm25_details["AQI"])
        category_name = str(category["Name"])
        hour_observed = pm25_details["HourObserved"]
        local_timezone = pm25_details["LocalTimeZone"]
    except (KeyError, TypeError, ValueError):
        fail(f"Unexpected PM2.5 data format for zipcode {zipcode}")

    if category_number >= threshold:
        aqi_color = get_aqi_color(aqi_value)
        colored_value = cast(Any, aqi_color)
        message = (
            f"[{colored(aqi_value, colored_value)}] "
            f"AirNow reports AQI for {zipcode} is "
            f"{colored(category_name, colored_value)} "
            f"as of {hour_observed}:00 {local_timezone}."
        )
        print(message)


def fetch_aqi_data(api_key: str, zipcode: str) -> list:
    payload = {
        "format": "application/json",
        "distance": "5",
        "zipCode": zipcode,
        "API_KEY": api_key,
    }

    response: Optional[requests.Response] = None
    try:
        response = requests.get(
            AQI_API,
            params=payload,
            proxies=proxies,
            timeout=10,
        )
    except requests.exceptions.RequestException as exc:
        fail(
            "Could not reach the API. Hint: Are you connected to the "
            "Internet? "
            f"({exc})"
        )

    assert response is not None

    if response.status_code != 200:
        fail(
            "API request failed with status "
            f"{response.status_code}: {response.reason}"
        )

    response_data: object
    try:
        response_data = response.json()
    except ValueError:
        fail("Invalid JSON response from API")

    if not isinstance(response_data, list):
        fail("Unexpected AQI response format from API")

    return cast(list, response_data)


def main() -> None:
    try:
        args = docopt(__doc__, version="0.1")
    except DocoptExit as exc:
        print(str(exc).strip(), file=sys.stderr)
        sys.exit(1)

    api_key, default_zipcode = load_configuration()
    zipcode = args["<zipcode>"] or default_zipcode
    setup_cache()
    aqi_threshold = get_aqi_threshold(args)
    response_data = fetch_aqi_data(api_key, zipcode)
    process_aqi_data(response_data, zipcode, aqi_threshold)


if __name__ == "__main__":
    main()
