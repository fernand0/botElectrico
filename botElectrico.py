#!/usr/bin/env python

import argparse
import datetime
import logging
import sys

from config import CACHE_DIR, clock
from data_handler import get_data, safe_get
from price_calculator import (
    get_price_and_next,
    get_price_trend_symbol,
    convert_time_to_datetime,
    get_time_frame,
    find_min_max_prices,
    generate_message
)
from visualizer import (
    generate_table,
    generate_chart_js,
    generate_plotly_graph,
    generate_matplotlib_graph
)
from social_media import (
    generar_resumen_diario,
    publicar_mensaje_horario,
    get_social_media_destinations
)

# Import socialModules with error handling for cases where it's not available
try:
    import socialModules
    import socialModules.moduleRules
except ImportError:
    socialModules = None
    logging.warning("socialModules not found. Some social media functionality may be limited.")

logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format="%(asctime)s %(message)s"
)


def parse_arguments():
    """Analiza los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Procesa argumentos para el script.")

    parser.add_argument("-s", action="store_true", help="Activa el modo de simulación.")
    parser.add_argument(
        "-t", nargs="?", const="21:00", help="Establece la hora (formato HH:MM)."
    )

    return parser.parse_args()


def file_name(now: datetime.datetime) -> str:
    return f"{now.year}-{now.month:02d}-{now.day:02d}"


def main() -> None:
    mode = None
    now = None
    args = parse_arguments()

    if args.s:
        if args.t:
            t_now = args.t
        else:
            t_now = "21:00"
        now = convert_time_to_datetime(t_now)
    elif not now:
        now = datetime.datetime.now()

    data = get_data(now)
    if not data:
        logging.error("Failed to retrieve data. Exiting.")
        return

    time_frame_info = get_time_frame(now)
    min_max_prices = find_min_max_prices(data, time_frame_info[2])
    message = generate_message(now, data, time_frame_info, min_max_prices)

    if len(message) > 280:
        logging.warning("Message too long. Truncating.")
        message = message[:280]

    if socialModules is None:
        logging.error("socialModules not available. Cannot post to social media.")
        return

    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules()

    destinations = get_social_media_destinations(args.s)
    logging.info(f"Destinations: {destinations}")

    if now.hour == 21:
        generar_resumen_diario(now, destinations, rules, message)
    else:
        publicar_mensaje_horario(destinations, message, rules)


if __name__ == "__main__":
    main()
