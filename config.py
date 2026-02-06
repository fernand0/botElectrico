"""Configuration module for botElectrico."""

import os
from typing import Dict, Any

# API settings
API_BASE: str = "https://apidatos.ree.es/"
API_URL: str = "https://api.esios.ree.es/archives/70/download_json"

# Time ranges for different tariff periods
TIME_RANGES: Dict[str, list[str]] = {
    "llano1": ["08:00", "10:00"],
    "punta1": ["10:00", "14:00"],
    "llano2": ["14:00", "18:00"],
    "punta2": ["18:00", "22:00"],
    "llano3": ["22:00", "24:00"],
    "valle": ["00:00", "08:00"],
}

# Symbols for different tariff periods
BUTTON_SYMBOLS: Dict[str, str] = {"llano": "🟠", "valle": "🟢", "punta": "🔴"}

# Cache directory
CACHE_DIR: str = os.getenv("BOT_ELECTRICO_CACHE_DIR", "/tmp")

# Clock emojis for hourly representation
clock: list[str] = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]

# Social media destinations
SOCIAL_MEDIA_DESTINATIONS: Dict[str, Dict[str, Any]] = {
    "twitter": {
        "test_account": "fernand0Test",
        "production_account": "botElectrico"
    },
    "telegram": {
        "test_account": "testFernand0",
        "production_account": "botElectrico"
    },
    "mastodon": {
        "test_account": "@fernand0Test@fosstodon.org",
        "production_account": "@botElectrico@mas.to"
    },
    "bluesky": {
        "test_account": "fernand0test.bsky.social",
        "production_account": "botElectrico.bsky.social"
    }
}
