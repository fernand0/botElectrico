#!/usr/bin/env python

import argparse
import datetime
import json
import logging
import os
import requests
import sys
import time

import matplotlib.pyplot as plt
import matplotlib.ticker
import pandas as pd
from plotly import express as px

from socialModules.configMod import getApi

API_BASE = "https://apidatos.ree.es/"
CLOCK_SYMBOLS = ["", "", "", "", "", "", "", "", "", "", "", ""]
TIME_RANGES = {
    "llano1": ["08:00", "10:00"],
    "punta1": ["10:00", "14:00"],
    "llano2": ["14:00", "18:00"],
    "punta2": ["18:00", "22:00"],
    "llano3": ["22:00", "24:00"],
    "valle": ["00:00", "08:00"],
}
BUTTON_SYMBOLS = {"llano": "🟠", "valle": "🟢", "punta": ""}
CACHE_DIR = "/tmp"

logging.basicConfig(
    stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
)

def parse_arguments():
    """Analiza los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Procesa argumentos para el script.")

    parser.add_argument("-s", action="store_true", help="Activa el modo de simulación.")
    parser.add_argument("-t", nargs="?", const="21:00", help="Establece la hora (formato HH:MM).")

    return parser.parse_args()

def get_cached_data(filepath):
    """Retrieves data from a cached file."""
    if os.path.exists(filepath):
        logging.info("Retrieving cached data.")
        with open(filepath, "r") as f:
            return json.load(f)
    return None


def fetch_api_data(url):
    """Fetches data from the API with retry logic."""
    data = None
    while not data:
        try:
            result = requests.get(url)
            result.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = json.loads(result.content)
            if "errors" not in data and "PVPC" in data:
                return data
            else:
                data = None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data: {e}")
        logging.info("Waiting to see if data becomes available.")
        time.sleep(300)
    return None


def save_data_to_cache(filepath, data):
    """Saves data to a cached file."""
    with open(filepath, "w") as f:
        json.dump(data, f)


def get_data(now):
    """Retrieves PVPC data, either from cache or API."""
    filepath = os.path.join(
        CACHE_DIR, f"{now.year}-{now.month:02d}-{now.day:02d}_data.json"
    )
    cached_data = get_cached_data(filepath)
    if cached_data:
        return cached_data

    url = "https://api.esios.ree.es/archives/70/download_json"  # simplified the URL
    data = fetch_api_data(url)
    if data:
        save_data_to_cache(filepath, data)
        return data
    return None


def get_price_and_next(data, hour):
    """Retrieves the current and next hour's prices."""
    current_price = float(data["PVPC"][hour]["PCB"].replace(",", ".")) / 1000
    next_hour = hour + 1
    if next_hour < 24:
        next_price = float(data["PVPC"][next_hour]["PCB"].replace(",", ".")) / 1000
    else:
        next_day = datetime.datetime.now() + datetime.timedelta(hours=1)
        next_day_data = get_data(next_day)
        next_price = float(next_day_data["PVPC"][0]["PCB"].replace(",", ".")) / 1000
    return current_price, next_price


def get_price_trend_symbol(current_price, next_price):
    """Determines the price trend symbol."""
    if next_price > current_price:
        return "↗"
    elif next_price < current_price:
        return "↘"
    else:
        return "↔"


def convert_time_to_datetime(time_str):
    """Converts a time string to a datetime object."""
    now = datetime.datetime.now().date()
    if time_str == "24:00":
        now += datetime.timedelta(days=1)
        time_str = "00:00"
    return datetime.datetime.strptime(f"{now} {time_str}", "%Y-%m-%d %H:%M")


def get_time_frame(now, weekday):
    """Determines the current time frame."""
    if weekday > 4:
        frame = ["00:00", "24:00"]
        frame_type = "valle"
        start = convert_time_to_datetime(frame[0])
        end = convert_time_to_datetime(frame[1])
    else:
        for frame_type, frame in TIME_RANGES.items():
            start = convert_time_to_datetime(frame[0])
            end = convert_time_to_datetime(frame[1])
            if start <= now < end:
                break
    return ( 
            start, 
            end, 
            frame, 
            frame_type if not frame_type[-1].isdigit() else frame_type[:-1],
            )

def find_min_max_prices(data, hours):
    """Finds the min and max prices within a given time range."""
    start_hour = int(hours[0].split(":")[0])
    end_hour = int(hours[1].split(":")[0]) if hours[1] != "00:00" else 24
    prices = [
        float(val["PCB"].replace(",", ".")) / 1000
        for val in data["PVPC"][start_hour:end_hour]
    ]
    min_price, max_price = min(prices), max(prices)
    min_index, max_index = prices.index(min_price), prices.index(max_price)
    return (start_hour + min_index, min_price), (start_hour + max_index, max_price)


def generate_message(now, data, time_frame_info, min_max_prices):
    """Generates the message to be published."""
    start, end, hours, frame_name = time_frame_info
    current_price, next_price = get_price_and_next(data, now.hour)
    price_trend = get_price_trend_symbol(current_price, next_price)
    range_msg = (
        f"(entre las {hours[0]} y las {hours[1]})"
        if frame_name != "valle"
        else "(entre las 00:00 y las 8:00)" if now.weekday() <= 4 else "(todo el día)"
    )
    message = f"{BUTTON_SYMBOLS[frame_name]} {'Empieza' if now.hour == start.hour else 'Estamos en'} periodo {frame_name} {range_msg}. Precios PVPC\n"
    message += f"En esta hora: {current_price:.3f}\nEn la hora siguiente: {next_price:.3f}{price_trend}\n"
    hour_time_frame_info = time_frame_info[0].hour
    if (hour_time_frame_info == now.hour) and min_max_prices:
        min_hour, min_price = min_max_prices[0]
        max_hour, max_price = min_max_prices[1]
        message += f"Mín: {min_price:.3f}, entre las {min_hour}:00 y las {min_hour + 1}:00 (hora más económica)\n"
        message += f"Máx: {max_price:.3f}, entre las {max_hour}:00 y las {max_hour + 1}:00 (hora más cara)"
    return message


def main():
    mode = None
    now = None
    # if len(sys.argv) > 1:
    #     if sys.argv[1] == "-t":
    #         mode = "test"
    #         if len(sys.argv) > 2:
    #             now = convert_time_to_datetime(sys.argv[2])
    args = parse_arguments()
    print(args)

    if args.s:
        if args.t:
            t_now = args.t
        else:
            t_now = "21:00" 
        now = convert_time_to_datetime(t_now)
    elif not now:
        now = datetime.datetime.now()
    print(f"Now: {now}")

    weekday = now.weekday()
    data = get_data(now)
    if not data:
        logging.error("Failed to retrieve data. Exiting.")
        return

    time_frame_info = get_time_frame(now, weekday)
    min_max_prices = find_min_max_prices(data, time_frame_info[2])
    message = generate_message(now, data, time_frame_info, min_max_prices)

    if len(message) > 280:
        logging.warning("Message too long. Truncating.")
        message = message[:280]

    destinations = {
        "twitter": "fernand0Test" if args.s else "botElectrico",
        "telegram": "testFernand0" if args.s else "botElectrico",
        "mastodon": "@fernand0Test@fosstodon.org" if args.s else "@botElectrico@mas.to",
        "blsk": None if args.s else "botElectrico.bsky.social",
    }
    logging.info(f"Destinations: {destinations}")

    for destination, account in destinations.items():
        logging.info(f"Destination: {account}@{destination}")
        api = getApi(destination, account)
        if api.getClient():
            result = api.publishPost(message, "", "")
            logging.info(f"Result: {result}")


if __name__ == "__main__":
    main()
