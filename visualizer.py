"""Module for visualization and graph generation."""

import datetime
from typing import Tuple, List, Dict, Any

import matplotlib.pyplot as plt
import matplotlib.ticker
import pandas as pd
from plotly import express as px

from config import clock, CACHE_DIR
from price_calculator import get_price_trend_symbol


def generate_table(values: List[float], min_day: Tuple[int, float], max_day: Tuple[int, float]) -> str:
    """Generates a table string from price values."""
    table = ""
    for i, price in enumerate(values):
        price_text = f"{clock[i % 12]} ({i:02d}:00) "
        if i > 0:
            prev_price = values[i - 1]
            price_text += f"{get_price_trend_symbol(price, prev_price)} "
        price_text += f"{price:.3f}"
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




def generate_chart_js(values: List[float], min_day: Tuple[int, float], max_day: Tuple[int, float], now_next: str) -> str:
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


def generate_plotly_graph(prices: List[float], now_next: datetime.datetime) -> None:
    """Generates and saves a Plotly graph to HTML."""
    # prices = [float(val['PCB'].replace(',', '.')) / 1000 for val in data["PVPC"]]
    max_price, min_price = max(prices), min(prices)
    max_index, min_index = prices.index(max_price), prices.index(min_price)
    df = pd.DataFrame({"Hora": range(len(prices)), "Precio": prices})
    fig = px.line(
        df,
        x="Hora",
        y="Precio",
        markers=True,
        title=f"[@botElectrico] PVPC. Evolución precio para el día {str(now_next).split(' ')[0]}",
    )
    fig.add_annotation(
        x=max_index,
        y=max_price,
        text=f"{max_price:.3f}",
        font=dict(color="#ffffff"),
        bgcolor="tomato",
        arrowcolor="tomato",
        showarrow=True,
        xanchor="right",
    )
    fig.add_annotation(
        x=min_index,
        y=min_price,
        text=f"{min_price:.3f}",
        font=dict(color="#ffffff"),
        bgcolor="MediumSeaGreen",
        arrowcolor="MediumSeaGreen",
        showarrow=True,
        xanchor="left",
    )
    with open("/tmp/plotly_graph.html", "w") as f:
        f.write(fig.to_html(include_plotlyjs="cdn", full_html=False))


def generate_matplotlib_graph(values: List[float], now_next: datetime.datetime) -> Tuple[str, Tuple[int, float], Tuple[int, float]]:
    """Generates and saves a Matplotlib graph to PNG and SVG."""
    max_price, min_price = max(values), min(values)
    max_index, min_index = values.index(max_price), values.index(min_price)
    plt.title(f"Evolución precio para el día {str(now_next).split(' ')[0]}")
    plt.ylim(min_price - 0.10, max_price + 0.10)
    plt.xlabel("Horas")
    plt.ylabel("Precio")
    plt.xticks(range(0, 24, 4))
    plt.gca().xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:.2f}"))
    arrowprops = dict(arrowstyle="simple", linewidth=0.0001, color="paleturquoise")
    plt.annotate(
        f"Max: {max_price:.3f} ({max_index}:00)",
        xy=(max_index, max_price),
        xytext=(0, max_price - 0.002),
        arrowprops=arrowprops,
    )
    plt.annotate(
        f"Min: {min_price:.3f} ({min_index}:00)",
        xy=(min_index, min_price),
        xytext=(0.5, max_price - 0.01),
        arrowprops=arrowprops,
    )
    plt.plot(values)
    png_path = (
        f"{CACHE_DIR}/{now_next.year}-{now_next.month:02d}-{now_next.day:02d}_image.png"
    )
    svg_path = (
        f"{CACHE_DIR}/{now_next.year}-{now_next.month:02d}-{now_next.day:02d}_image.svg"
    )
    plt.savefig(png_path)
    plt.savefig(svg_path)
    plt.close()
    return png_path, (min_index, min_price), (max_index, max_price)