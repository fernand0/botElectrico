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
BUTTON_SYMBOLS = {"llano": "🟠", "valle": "🟢", "punta": "🔴"}
CACHE_DIR = "/tmp"

clock = ['🕛', '🕐', '🕑', '🕒', '🕓', '🕔', 
         '🕕', '🕖', '🕗', '🕘', '🕙', '🕚']

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

def generate_table(values, min_day, max_day):
    """Generates a table string from price values."""
    table = ""
    for i, price in enumerate(values):
        prev_price = values[i - 1] if i > 0 else 1000  # FIXME: Handle first element
        price_text = f"{CLOCK_SYMBOLS[i % 12]} ({i:02d}:00) {get_price_trend_symbol(price, prev_price)} {price:.3f}"
        color = ""
        if i == max_day[0]:
            color = "Tomato"
        if i == min_day[0]:
            color = "MediumSeaGreen"
        if color:
            price_text = f"<span style='border:2px solid {color};'>{price_text}</span>"
        table += f"| {price_text} "
        if (i + 1) % 4 == 0:
            table += "|\n"
    return table + "\n"

def generate_chart_js(values, min_day, max_day, now_next):
    """Generates JavaScript code for a Chart.js chart."""
    js = f"""
        import Chart from 'chart.js/auto';
        import annotationPlugin from 'chartjs-plugin-annotation';
        Chart.register(annotationPlugin);
        (async function() {{
            const data = [{', '.join([f'{{hour: {i}, pvpc: {price} }}' for i, price in enumerate(values)])}];
            new Chart(document.getElementById('acquisitions'), {{
                type: 'line',
                options: {{
                    animation: false,
                    plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: false }} }},
                    annotation: {{
                        annotations: {{
                            point1: {{ type: 'point', xValue: {min_day[0]}, yValue: {min_day[1]}, backgroundColor: 'rgba(255, 99, 132, 0.25)' }},
                            label1: {{ type: 'label', backgroundColor: 'rgba(245,245,245)', xValue: {min_day[0]}, yValue: {min_day[1]}, xAdjust: 100, yAdjust: -200, content: ['Min: {min_day[1]} ({min_day[0]}:00)'], textAlign: 'start', callout: {{ display: true, side: 10 }} }},
                            point2: {{ type: 'point', xValue: {max_day[0]}, yValue: {max_day[1]}, backgroundColor: 'rgba(255, 99, 132, 0.25)' }},
                            label2: {{ type: 'label', backgroundColor: 'rgba(245,245,245)', xValue: {max_day[0]}, yValue: {max_day[1]}, xAdjust: -300, yAdjust: -100, content: ['Max: {max_day[1]} ({max_day[0]}:00)'], textAlign: 'start', callout: {{ display: true, side: 10 }} }}
                        }}
                    }}
                }},
                data: {{ labels: data.map(row => row.hour), datasets: [{{ label: 'Evolución precio para el día {now_next}', data: data.map(row => row.pvpc) }}] }}
            }});
        }})();
    """
    return js

def generate_plotly_graph(data, now_next):
    """Generates and saves a Plotly graph to HTML."""
    prices = [float(val['PCB'].replace(',', '.')) / 1000 for val in data["PVPC"]]
    max_price, min_price = max(prices), min(prices)
    max_index, min_index = prices.index(max_price), prices.index(min_price)
    df = pd.DataFrame({'Hora': range(len(prices)), 'Precio': prices})
    fig = px.line(df, x='Hora', y='Precio', markers=True, title=f"[@botElectrico] PVPC. Evolución precio para el día {str(now_next).split(' ')[0]}")
    fig.add_annotation(x=max_index, y=max_price, text=f"{max_price:.3f}", font=dict(color="#ffffff"), bgcolor="tomato", arrowcolor="tomato", showarrow=True, xanchor="right")
    fig.add_annotation(x=min_index, y=min_price, text=f"{min_price:.3f}", font=dict(color="#ffffff"), bgcolor="MediumSeaGreen", arrowcolor="MediumSeaGreen", showarrow=True, xanchor="left")
    with open('/tmp/plotly_graph.html', 'w') as f:
        f.write(fig.to_html(include_plotlyjs='cdn', full_html=False))

def generate_matplotlib_graph(values, now_next):
    """Generates and saves a Matplotlib graph to PNG and SVG."""
    max_price, min_price = max(values), min(values)
    max_index, min_index = values.index(max_price), values.index(min_price)
    plt.title(f"Evolución precio para el día {str(now_next).split(' ')[0]}")
    plt.ylim(min_price - 0.10, max_price + 0.10)
    plt.xlabel("Horas")
    plt.ylabel("Precio")
    plt.xticks(range(0, 24, 4))
    plt.gca().xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:.2f}"))
    arrowprops = dict(arrowstyle='simple', linewidth=0.0001, color='paleturquoise')
    plt.annotate(f'Max: {max_price:.3f} ({max_index}:00)', xy=(max_index, max_price), xytext=(0, max_price - 0.002), arrowprops=arrowprops)
    plt.annotate(f'Min: {min_price:.3f} ({min_index}:00)', xy=(min_index, min_price), xytext=(0.5, max_price - 0.01), arrowprops=arrowprops)
    plt.plot(values)
    png_path = f"{CACHE_DIR}/{now_next.year}-{now_next.month:02d}-{now_next.day:02d}_image.png"
    svg_path = f"{CACHE_DIR}/{now_next.year}-{now_next.month:02d}-{now_next.day:02d}_image.svg"
    plt.savefig(png_path)
    plt.savefig(svg_path)
    plt.close()
    return png_path, (min_index, min_price), (max_index, max_price), values


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

    if len(message) > 280:
        logging.warning("Message too long. Truncating.")
        message = message[:280]

    destinations = {
        "twitter": "fernand0Test" if mode == 'test' else "botElectrico",
        "telegram": "testFernand0" if mode == 'test' else "botElectrico",
        "mastodon": "@botElectrico@mas.to",
        "blsk": "botElectrico.bsky.social"
    }
    logging.info(f"Destinations: {destinations}")

    if now.hour == 21:
        next_day = now + datetime.timedelta(days=1)
        next_day_data = get_data(next_day)
        png_path, min_day, max_day, values = generate_matplotlib_graph(
            [float(val['PCB'].replace(',', '.')) / 1000 for val in next_day_data["PVPC"]], next_day)
        generate_plotly_graph(next_day_data, next_day)
        table = generate_table(values, min_day, max_day)
        js_code = generate_chart_js(values, min_day, max_day, str(next_day).split(' ')[0])
        with open(f"/tmp/kk.js", 'w') as f:
            f.write(js_code)

        date_post = str(now).split(' ')[0]
        date_next_day = str(next_day).split(' ')[0]
        title = f"Evolución precio para el día {date_next_day}"
        alt_text = f"{title}. Mínimo a las {min_day[0]}:00 ({min_day[1]:.3f}). Máximo a las {max_day[0]}:00 ({max_day[1]:.3f})."
        markdown_content = f"""
            ---
            layout: post
            title: '{title}'
            date: {date_post} 21:00:59 +0200
            categories: jekyll update
            ---
            {alt_text}
            {open(f"{png_path[:-4]}.svg", 'r').read()}
            {open('/tmp/plotly_graph.html', 'r').read()}
            {table}
        """
        with open(f"{CACHE_DIR}/{now.year}-{now.month:02d}-{now.day:02d}-post.md", 'w') as f:
            f.write(markdown_content)

        return
        for destination, account in destinations.items():
            api = getApi(destination, account)
            try:
                result = api.publishImage(title, png_path, alt=alt_text)
                if hasattr(api, 'lastRes') and api.lastRes and 'media_attachments' in api.lastRes and api.lastRes['media_attachments'] and 'url' in api.lastRes['media_attachments'][0]:
                    image_url = api.lastRes['media_attachments'][0]['url']
                else:
                    image_url = None
            except Exception as e:
                logging.error(f"Failed to publish image to {destination}: {e}")
                image_url = None

            api.publishPost(message, "", "")
            logging.info(f"Published to {destination}: {result}")
    else:
        for destination, account in destinations.items():
            api = getApi(destination, account)
            result = api.publishPost(message, "", "")
            logging.info(f"Published to {destination}: {result}")


if __name__ == "__main__":
    main()
