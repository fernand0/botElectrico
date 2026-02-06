"""Module for data fetching and caching functionality."""

import datetime
import json
import logging
import os
import requests
import time
from typing import Dict, Any, Optional, Union

from config import API_URL, CACHE_DIR

def safe_get(data: Dict[str, Any], keys: list, default: Any = "") -> Any:
    """Safely retrieves nested values from a dictionary."""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default


def file_name(now: datetime.datetime) -> str:
    """Generate filename based on date."""
    return f"{now.year}-{now.month:02d}-{now.day:02d}"


def get_cached_data(filepath: str) -> Optional[Dict[str, Any]]:
    """Retrieves data from a cached file."""
    if os.path.exists(filepath):
        logging.info("Retrieving cached data.")
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error reading cached data from {filepath}: {e}")
            return None
    return None


def fetch_api_data(url: str) -> Optional[Dict[str, Any]]:
    """Fetches data from the API with retry logic."""
    retries = 3
    while retries > 0:
        try:
            logging.info(f"Attempting to fetch data from {url}")
            result = requests.get(url, timeout=30)
            result.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = json.loads(result.content)
            if "errors" not in data and "PVPC" in data:
                logging.info("Successfully fetched data from API")
                return data
            else:
                logging.warning(f"API response contains errors or missing PVPC data: {data.get('errors', 'PVPC data missing')}")
        except requests.exceptions.Timeout:
            logging.error(f"Request timed out while fetching data from {url}")
        except requests.exceptions.ConnectionError:
            logging.error(f"Connection error while fetching data from {url}")
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error while fetching data: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error in API response: {e}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Unexpected error fetching data: {e}")
        
        logging.info("Waiting to see if data becomes available.")
        time.sleep(300)
        retries -= 1
    
    logging.error("Failed to fetch valid data after all retries")
    return None


def save_data_to_cache(filepath: str, data: Dict[str, Any]) -> None:
    """Saves data to a cached file."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f)
        logging.info(f"Data successfully saved to cache: {filepath}")
    except IOError as e:
        logging.error(f"Error saving data to cache {filepath}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error saving data to cache {filepath}: {e}")


def get_data(now: datetime.datetime) -> Optional[Dict[str, Any]]:
    """Retrieves PVPC data, either from cache or API."""
    try:
        filepath = os.path.join(CACHE_DIR, f"{file_name(now)}_data.json")
        data = get_cached_data(filepath)
        if not data:
            logging.info(f"No cached data found at {filepath}, fetching from API")
            data = fetch_api_data(API_URL)
            if data:
                save_data_to_cache(filepath, data)
            else:
                logging.error("Could not retrieve data from either cache or API")
        else:
            logging.info(f"Using cached data from {filepath}")
        
        return data
    except Exception as e:
        logging.error(f"Unexpected error in get_data: {e}")
        return None