"""Module for price calculation and time frame logic."""

import datetime
from typing import Tuple, Dict, Any, List

from config import BUTTON_SYMBOLS, TIME_RANGES
from data_handler import get_data, safe_get


def get_price_and_next(data: Dict[str, Any], now: datetime.datetime) -> Tuple[float, float]:
    """Retrieves the current and next hour's prices."""
    try:
        price = safe_get(data, ['PVPC', now.hour, 'PCB'])
        if not price:
            raise ValueError(f"No price data available for hour {now.hour}")
        
        current_price = float(price.replace(",", ".")) / 1000
        next_now = now + datetime.timedelta(hours=1)
        if next_now.day == now.day:
            next_data = data
        else:
            next_data = get_data(next_now)
            if not next_data:
                raise ValueError(f"Could not retrieve data for next hour {next_now.hour}")
        
        price = safe_get(next_data, ['PVPC', next_now.hour, 'PCB'])
        if not price:
            raise ValueError(f"No price data available for next hour {next_now.hour}")
        
        next_price = float(price.replace(",", ".")) / 1000
        
        return current_price, next_price
    except ValueError as e:
        logging.error(f"Value error in get_price_and_next: {e}")
        # Return default values in case of error
        return 0.0, 0.0
    except Exception as e:
        logging.error(f"Unexpected error in get_price_and_next: {e}")
        # Return default values in case of error
        return 0.0, 0.0


def get_price_trend_symbol(current_price: float, next_price: float) -> str:
    """Determines the price trend symbol."""
    if next_price > current_price:
        symbol = "↗"
    elif next_price < current_price:
        symbol = "↘"
    else:
        symbol = "↔"

    return symbol


def convert_time_to_datetime(time_str: str) -> datetime.datetime:
    """Converts a time string to a datetime object."""
    try:
        now = datetime.datetime.now().date()
        if time_str == "24:00":
            now += datetime.timedelta(days=1)
            time_str = "00:00"
        return datetime.datetime.strptime(f"{now} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError as e:
        logging.error(f"Invalid time format {time_str}: {e}")
        # Return current time if parsing fails
        return datetime.datetime.now()
    except Exception as e:
        logging.error(f"Unexpected error converting time {time_str}: {e}")
        # Return current time if parsing fails
        return datetime.datetime.now()


def get_time_frame(now: datetime.datetime) -> Tuple[datetime.datetime, datetime.datetime, List[str], str]:
    """Determines the current time frame."""
    weekday = now.weekday()
    start = ''
    end = ''
    if weekday > 4:
        # Weekend
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


def find_min_max_prices(data: Dict[str, Any], frame: List[str]) -> Tuple[Tuple[int, float], Tuple[int, float]]:
    """Finds the min and max prices within a given time range."""
    try:
        if not data or "PVPC" not in data:
            raise ValueError("Invalid data format: missing PVPC data")
        
        start_hour = int(frame[0].split(":")[0])
        end_hour = int(frame[1].split(":")[0]) if frame[1] != "00:00" else 24
        
        if start_hour < 0 or start_hour > 23 or end_hour < 0 or end_hour > 24:
            raise ValueError(f"Invalid hour range: start={start_hour}, end={end_hour}")
        
        pvpc_data = data["PVPC"]
        if start_hour >= len(pvpc_data) or (end_hour > 0 and end_hour-1 >= len(pvpc_data)):
            raise IndexError(f"Hour index out of range for PVPC data with length {len(pvpc_data)}")
        
        prices = []
        for i in range(start_hour, end_hour):
            if i < len(pvpc_data):
                val = pvpc_data[i]
                if "PCB" in val:
                    try:
                        price = float(val["PCB"].replace(",", ".")) / 1000
                        prices.append(price)
                    except (ValueError, AttributeError):
                        logging.warning(f"Invalid price data for hour {i}: {val}")
                        # Append a default value or skip
                        continue
                else:
                    logging.warning(f"Missing PCB data for hour {i}")
        
        if not prices:
            raise ValueError("No valid price data found in the specified time range")
        
        min_price, max_price = min(prices), max(prices)
        min_index = prices.index(min_price)
        max_index = prices.index(max_price)
        
        return ((start_hour + min_index, min_price),
                (start_hour + max_index, max_price))
    except ValueError as e:
        logging.error(f"Value error in find_min_max_prices: {e}")
        # Return default values in case of error
        return ((0, 0.0), (0, 0.0))
    except Exception as e:
        logging.error(f"Unexpected error in find_min_max_prices: {e}")
        # Return default values in case of error
        return ((0, 0.0), (0, 0.0))


def generate_message(now: datetime.datetime, data: Dict[str, Any], time_frame_info: tuple, min_max_prices: tuple) -> str:
    """Generates the message to be published."""
    try:
        start, end, frame, frame_name = time_frame_info
        current_price, next_price = get_price_and_next(data, now)
        price_trend = get_price_trend_symbol(current_price, next_price)
        range_msg = (
            f"(entre las {frame[0]} y las {frame[1]})"
            if frame_name != "valle"
            else "(entre las 00:00 y las 8:00)" if now.weekday() <= 4
            else "(todo el día)"
        )
        message = (f"{BUTTON_SYMBOLS.get(frame_name, '?')} "
                   f"{'Empieza' if now.hour == start.hour else 'Estamos en'} "
                   f"periodo {frame_name} {range_msg}. Precios PVPC\n"
                   )
        message += (f"En esta hora: {current_price:.3f}\n"
                    f"En la hora siguiente: {next_price:.3f}{price_trend}\n"
                    )
        if (start.hour == now.hour) and min_max_prices:
            min_hour, min_price = min_max_prices[0]
            max_hour, max_price = min_max_prices[1]
            message += (f"Mín: {min_price:.3f}, entre las {min_hour}:00 "
                        f"y las {min_hour + 1}:00 (hora más económica)\n"
                        )
            message += (f"Máx: {max_price:.3f}, entre las {max_hour}:00 "
                        f"y las {max_hour + 1}:00 (hora más cara)"
                        )
        return message
    except Exception as e:
        logging.error(f"Error generating message: {e}")
        # Return a default message in case of error
        return f"Error retrieving electricity price data: {str(e)}"