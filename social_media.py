"""Module for social media posting functionality."""

import datetime
import logging
from typing import Dict, Any, Tuple, List

# Import socialModules with error handling for cases where it's not available
try:
    import socialModules
    import socialModules.moduleRules
    from socialModules.configMod import getApi
except ImportError:
    socialModules = None
    getApi = None
    logging.warning("socialModules not found. Some social media functionality may be limited.")

from config import SOCIAL_MEDIA_DESTINATIONS, CACHE_DIR
from price_calculator import generate_message
from data_handler import get_data, file_name
from visualizer import generate_matplotlib_graph, generate_plotly_graph, generate_table, generate_chart_js


def generar_resumen_diario(now: datetime.datetime, destinations: Dict[str, str], rules: Any, message: str) -> None:
    """Generate daily summary and post to social media."""
    if socialModules is None:
        logging.error("socialModules not available. Cannot post to social media.")
        return
        
    next_day = now + datetime.timedelta(days=1)
    next_day_data = get_data(next_day)
    prices = [
        float(val["PCB"].replace(",", ".")) / 1000
        for val in next_day_data["PVPC"]
    ]
    png_path, min_day, max_day = generate_matplotlib_graph(prices, next_day)
    generate_plotly_graph(prices, next_day)
    table = generate_table(prices, min_day, max_day)
    js_code = generate_chart_js(
        prices, min_day, max_day, str(next_day).split(" ")[0]
    )
    with open(f"/tmp/kk.js", "w") as f:
        f.write(js_code)

    date_post = str(now).split(" ")[0]
    date_next_day = str(next_day).split(" ")[0]
    title = f"Evolución precio para el día {date_next_day}"
    alt_text = f"{title}. Mínimo a las {min_day[0]}:00 ({min_day[1]:.3f}). Máximo a las {max_day[0]}:00 ({max_day[1]:.3f})."
    image = open(f"{png_path[:-4]}.svg", "r").read()
    graph_html = open("/tmp/plotly_graph.html", "r").read()
    markdown_content = (
        f"---\n"
        "layout: post\n"
        f"title:  '{title}'\n"
        f"date:   {date_post} 21:00:59 +0200\n"
        "categories: jekyll update\n"
        "---\n\n"
        f"{alt_text}\n\n"
        "# f\"\\{image}\"\n\n"
        f"{graph_html}\n\n"
        f"{table}"
    )
    with open(
        f"{CACHE_DIR}/{file_name(now)}-post.md", "w"
    ) as f:
        f.write(markdown_content)

    for destination, account in destinations.items():
        logging.info(f" Now in: {destination} - {account}")
        if account:
            key = ("direct", "post", destination, account)
            # api = getApi(destination, account)
            indent = "  "
            api = rules.readConfigDst(indent, key, None, None)
            try:
                result = api.publishImage(title, png_path, alt=alt_text)
                if (
                    hasattr(api, "lastRes")
                    and api.lastRes
                    and "media_attachments" in api.lastRes
                    and api.lastRes["media_attachments"]
                    and "url" in api.lastRes["media_attachments"][0]
                ):
                    image_url = api.lastRes["media_attachments"][0]["url"]
                else:
                    image_url = None
            except Exception as e:
                logging.error(f"Failed to publish image to {destination}: {e}")
                image_url = None

            result = api.publishPost(message, "", "")
            logging.info(f"Published to {destination}: {result}")


def publicar_mensaje_horario(destinations: Dict[str, str], message: str, rules: Any) -> None:
    """Publish hourly message to social media."""
    if socialModules is None:
        logging.error("socialModules not available. Cannot post to social media.")
        return
        
    for destination, account in destinations.items():
        logging.info(f" Now in: {destination} - {account}")
        if account:
            key = ("direct", "post", destination, account)
            # api = getApi(destination, account)
            indent = "  "
            api = rules.readConfigDst(indent, key, None, None)
            result = api.publishPost(message, "", "")
            logging.info(f"Published to {destination}: {result}")


def get_social_media_destinations(is_simulation: bool = False) -> Dict[str, str]:
    """Get social media destinations based on simulation mode."""
    destinations: Dict[str, str] = {}
    for platform, accounts in SOCIAL_MEDIA_DESTINATIONS.items():
        if platform == "bluesky":
            # Special handling for bluesky due to different naming
            destinations["blsk"] = accounts["production_account"] if not is_simulation else accounts["test_account"]
        else:
            destinations[platform] = accounts["production_account"] if not is_simulation else accounts["test_account"]
    
    return destinations