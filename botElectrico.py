#!/usr/bin/env python

import datetime
import getpass
import json
import logging
import os
import requests
import sys

import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib.patches as patches

from socialModules.configMod import *

apiBase = "https://apidatos.ree.es/"

clock = ['🕛', '🕐', '🕑', '🕒', '🕓', '🕔', 
         '🕕', '🕖', '🕗', '🕘', '🕙', '🕚']

ranges = {
        "llano1": ["08:00", "10:00"], 
        "punta1": ["10:00", "14:00"], 
        "llano2": ["14:00", "18:00"], 
        "punta2": ["18:00", "22:00"], 
        "llano3": ["22:00", "24:00"], 
        "valle":  ["00:00", "8:00"] 
        }

button = {"llano": "🟠", "valle": "🟢", "punta": "🔴"}


def nameFile(now):
    return f"/tmp/{now.year}-{now.month:0>2}-{now.day:0>2}"

def getData(now):
    #print(now)
    name = f"{nameFile(now)}_data.json"
    logging.info(name)
    if os.path.exists(name):
        logging.info("Cached")
        data=json.loads(open(name).read())
    else:
        logging.info("Downloading")
        # https://pybonacci.org/2020/05/12/demanda-electrica-en-espana-durante-el-confinamiento-covid-19-visto-con-python/
        # https://api.esios.ree.es/
        # https://www.ree.es/es/apidatos
        # https://api.esios.ree.es/archives/70/download_json
        # dataJ = json.loads(data.text)
        # dataJ['PVPC'][0]
        urlPrecio = (
            f"{apiBase}es/datos/mercados/precios-mercados-tiempo-real?"\
            f'start_date={(now).strftime("%Y-%m-%dT00:00")}'\
            f'&end_date={(now).strftime("%Y-%m-%dT23:59")}'\
            f"&time_trunc=hour"
        )
        urlPrecio = "https://api.esios.ree.es/archives/70/download_json"
        data = None
        while not data:
            result = requests.get(urlPrecio)
            data = json.loads(result.content)
            if (('errors' not in data) and
                ('PVPC' in data)):
                # (data["included"][0]["attributes"]["title"].find('PVPC')>= 0)):
                    # When the PVPC is not ready the API serves
                    # "Precio mercado spot (\u20ac/MWh)", which
                    # is the prize paid to producers
                    with open(name, 'w') as f:
                        json.dump(data, f)
            else:
                data = None
            if not data:
                logging.info("Waiting to see if it is available later")
                import time
                time.sleep(300)

    return data

def nextSymbol(prize, prizeNext):
    if prizeNext > prize:
        nextSymbol = "↗"
    elif prizeNext < prize:
        nextSymbol = "↘"
    else:
        nextSymbol = "↔"

    return nextSymbol

def convertToDatetime(myTime):
    now = datetime.datetime.now()
    date = datetime.datetime.date(now)
    if myTime == '24:00':
        date = date + datetime.timedelta(days=1)
        converted = '00:00'
    else:
        converted = myTime
    converted = datetime.datetime.strptime(f"{date} {converted}",
                                           "%Y-%m-%d %H:%M")

    return converted

def makeTable(values, minDay, maxDay):
    hh = 0
    # text = "<table>"
    text = ""
    print(f"Values: {values}")
    for i, val in enumerate(values):
        if i - 1 >= 0:
            prevVal = values[i-1]
        else:
            prevVal = 1000 #FIXME
        text = (f"{text}|") 
        textt = (f"{clock[hh % 12]} ({hh:02}:00)"
                f"{nextSymbol(val, prevVal)} {val:.3f}"
                )
        color = ''
        if i == maxDay[0]:
            color = 'Tomato'
        if i == minDay[0]:
            color = 'MediumSeaGreen'
        if color:
            textt = f"<span style='border:2px solid {color};'>{textt}</span>"
        text = f"{text}{textt}"
        if (hh % 4 == 3):
            text = f"{text} | \n"
        hh = hh + 1
    text = f"{text} \n"

    logging.debug(f"New Table: \n{text}")

    return text

def makeJs(values, minDay, maxDay, nowNext):
   program = """
   import Chart from 'chart.js/auto'
   import annotationPlugin from 'chartjs-plugin-annotation';
    
   Chart.register(annotationPlugin);
    
   (async function() {

    const data = [
    """
   for i,val in enumerate(values):
        program = f"{program}\n{{hour: {i}, pvpc: {values[i]} }},"
        
   program = f"{program}\n ,];\n\n"

   program = f"""{program}

   new Chart(
    document.getElementById('acquisitions'),
    {{
      type: 'line',
      options: {{
        animation: false,
        plugins: {{
          legend: {{
            display: false
          }},
          tooltip: {{
            enabled: false
          }}
        }},
  	plugins: {{
  	  annotation: {{
  	    annotations: {{
  	      point1: {{
  	        type: 'point',
  	        xValue: {minDay[0]},
  	        yValue: {minDay[1]},
  	        backgroundColor: 'rgba(255, 99, 132, 0.25)'
          }},
	     label1: {{
		     type: 'label',
		     backgroundColor: 'rgba(245,245,245)',
		     xValue: {minDay[0]},
             yValue: {minDay[1]},
		     xAdjust: 100,
             yAdjust: -200,
		     content: ['Min: {minDay[1]} ({minDay[0]}:00)'],
		     textAlign: 'start',
	     	     callout: {{
            	         display: true,
            	         side: 10 
                 }}
         }},
	     point2: {{
  	        type: 'point',
  	        xValue: {maxDay[0]},
  	        yValue: {maxDay[1]},
  	        backgroundColor: 'rgba(255, 99, 132, 0.25)'
          }},

	     label2: {{
		     type: 'label',
		     backgroundColor: 'rgba(245,245,245)',
		     xValue: {maxDay[0]},
             yValue: {maxDay[1]},
		     xAdjust: -300,
             yAdjust: -100,
		     content: ['Max: {maxDay[1]} ({maxDay[0]}:00)'],
		     textAlign: 'start',
	     	     callout: {{
            	         display: true,
            	         side: 10 
                 }}
         }}
        }}
      }}
    }}
      }},
      data: {{
        labels: data.map(row => row.hour),
        datasets: [
          {{
            label: 'Evolución precio para el día {nowNext}',
            data: data.map(row => row.pvpc)
          }}
        ]
      }}
    }}
  );

}})();
"""

   return program

def graficaDiaPlot(data):
    from plotly import express as px
    import pandas as pd

    values=[float(val['PCB'].replace(',','.'))/1000
            for val in data["PVPC"]]

    for i, value in enumerate(values):
        csv = f"{csv}{i},{value}\n"
    
    import io
    df = pd.read_csv(io.StringIO(csv))
    
    fig = px.line(
            df, x='Hour', y='Value',
            title = "PVPC. Evolución precio para el día 2024-10-30"
    )
    
    with open('/tmp/plotly_graph.html', 'w') as f:
        f.write(fig.to_html(include_plotlyjs='cdn'))
    
    with open('/tmp/plotly_graph.png', 'wb') as f:
        f.write(fig.to_image(format='png'))


def graficaDia(now, nowNext, delta, data):

    values=[float(val['PCB'].replace(',','.'))/1000
            for val in data["PVPC"]]
            #for val in data["included"][0]["attributes"]["values"]]

    logging.debug(f"Values: {values}")

    plt.title(f"Evolución precio para el día {str(nowNext).split(' ')[0]}")

    maxy = 0.275
    miny = 0.010
    ymax = max(values)
    ymin = min(values)
    plt.ylim((ymin-0.10, ymax+0.10))
    plt.xlabel("Horas")
    plt.ylabel("Precio")
    plt.xticks(range(0, 23, 4))
    formatter = matplotlib.ticker.StrMethodFormatter("{x:.2f}")
    plt.gca().xaxis.set_major_formatter(formatter)

    ymax = max(values)
    xpos = values.index(ymax)
    xmax = xpos
    ymin = min(values)
    xpos = values.index(ymin)
    xmin = xpos
    maxDay = (xmax, ymax)
    minDay = (xmin, ymin)

    arrowprops = dict(arrowstyle='simple', linewidth=0.0001,
            color='paleturquoise')
    # linewidth cannot be a string ?

    posMax = ymax - 2/1000
    posMin = posMax - 10/1000
    if xmax < 8:
        posMax = posMax - 10/1000
        posMin = posMin - 10/1000

    plt.annotate(f'Max: {ymax:.3f} ({xmax}:00)', xy=(xmax,ymax),
            xytext=(0,posMax), arrowprops=arrowprops)
    plt.annotate(f'Min: {ymin:.3f} ({xmin}:00)', xy=(xmin,ymin),
            xytext=(0.5, posMin), arrowprops=arrowprops)
    plt.plot(values)
    name = f"{nameFile(nowNext)}_image.png"
    plt.savefig(name)
    name2 = f"{nameFile(nowNext)}_image.svg"
    plt.savefig(name2)


    return name, minDay, maxDay, values, nowNext

def masBarato(data, hours):
    startH = int(hours[0].split(':')[0])
    endH = int(hours[1].split(':')[0])
    if endH == '00':
        endH = '24'

    logging.info(f"start: {startH}, {endH}")
    # print(data)
    values=[float(val['PCB'].replace(',','.'))/1000
            for val in data["PVPC"]]
    #values = data["included"][0]["attributes"]["values"]

    # for val in [values[start*8:(start+1)*8] for start in range(3)]:
    maxI = 0
    maxV = 0
    minI = 0
    minV = 100000
    for i, hour in enumerate(values[startH: endH]):
        # logging.info(f"Hour: {hour}")
        if hour>maxV:
            maxV = hour
            maxI = startH + i
            hourMax = hour
        if hour<minV:
            minV = hour
            minI = startH + i
            hourMin = hour
    logging.info(f"Max {maxV} {maxI}")
    logging.info(f"Min {minV} {minI}")
    return((minI, hourMin), (maxI, hourMax))

def getPrices(data, hh):
    pos = int(hh)
    logging.info(f"Position: {pos}")

    prize = data["PVPC"][pos]["PCB"]

    if pos < 23:
        prizeNext = data["PVPC"][pos + 1]["PCB"]
    else:
        nextDay = now + datetime.timedelta(hours=1)
        dataNext = getData(nextDay)

        prizeNext = data["PVPC"][0]["PCB"]

    prize = float(prize.replace(',','.')) / 1000
    prizeNext = float(prizeNext.replace(',','.')) / 1000

    return prize, prizeNext

def checkTimeFrame(ranges, now, dd):
    if dd > 4:
        tipoHora = ''
        frame = ["00:00", "24:00"]
        start = convertToDatetime(frame[0])
        end = convertToDatetime(frame[1])
        frameType = "valle"
    else:
        for typeH in ranges:
            start = convertToDatetime(ranges[typeH][0])
            end = convertToDatetime(ranges[typeH][1])
            logging.info(f"Now: {now} Start:{start} End: {end}")

            frame = ranges[typeH]
            if ((start <= now) and (now < end)):
                if typeH[-1].isdigit():
                    # llano1, punta1, ....
                    frameType = typeH[:-1]
                else:
                    frameType = typeH

                tipoHora = typeH
                break

    return start, end, frameType, frame, tipoHora


def main():

    mode = None
    now = None
    if len(sys.argv) > 1:
        if sys.argv[1] == '-t':
            mode = 'test'
            if (len(sys.argv) > 2):
                now = convertToDatetime(sys.argv[2])

    logging.basicConfig(
            stream=sys.stdout, level=logging.DEBUG,
            format="%(asctime)s %(message)s"
            )

    if mode == 'test':
        if not now:
            now = convertToDatetime("21:00")
    elif not now:
        now = datetime.datetime.now()
    # now = convertToDatetime("21:00")
    # print(now)

    dd = now.weekday()
    hh = now.hour
    mm = now.minute

    data = getData(now)
    # Trying to catch errors in obtaining data

    prize, prizeNext = getPrices(data, hh)

    luego = ''
    empiezaTramo = False
    minData = None

    now = datetime.datetime.now()

    start, end, frameType, frame, tipoHora = checkTimeFrame(ranges, now, dd)
    minData, maxData = masBarato(data, frame)

    if minData:
        logging.info(f"minData: {minData}")
        timeMin = minData[0]
        timeMax = maxData[0]

    if hh == start.hour:
        empiezaTramo = True
        msgBase1 = "Empieza"
    else:
        msgBase1 = "Estamos en"
    msgBase1 = f"{msgBase1} periodo {frameType}"

    timeGraph = 21
    if hh == timeGraph:
        delta = 24 - timeGraph
        nowNext = now + datetime.timedelta(hours=delta)
        dataNext = getData(nowNext)
        nameGraph, minDay, maxDay, values, nowNext = graficaDia(now, 
                                                                nowNext,
                                                                delta,
                                                                dataNext)
        try:
            graficaDiaPlot(data)
        except:
            print("Some problem")
        table = makeTable(values, minDay, maxDay)
        js = makeJs(values, minDay, maxDay, str(nowNext).split(' ')[0])
        with open(f"/tmp/kk.js", 'w') as f:
            f.write(js)

    if frameType == "valle":
        if dd <= 4:
            msgFranja = "(entre las 00:00 y las 8:00)"
        else:
            msgFranja = "(todo el día)"
    else:
        msgFranja = (f"(entre las {ranges[tipoHora][0]} "
                     f"y las {ranges[tipoHora][1]})")

    msgBase1 = f"{msgBase1} {msgFranja}. Precios PVPC"

    msgPrecio = (
            f"\nEn esta hora: {prize:.3f}"# {tipo}"
            f"\nEn la hora siguiente: "
            f"{prizeNext:.3f}{nextSymbol(prize, prizeNext)}"
            )

    if empiezaTramo:
        prizeMin = minData[1]
        prizeMax = maxData[1]
        msgMaxMin = (
                     f"\nMín: {prizeMin:.3f}, entre las {timeMin} y "
                     f"las {timeMin+1} (hora más económica)"
                     f"\nMáx: {prizeMax:.3f}, entre las {timeMax} y "
                     f"las {timeMax+1} (hora más cara)"
                     )
        msgBase1 = f"{msgBase1}{msgMaxMin}"
    msgBase1 = (
            f"{button[frameType]} {msgBase1}"
            f"{msgPrecio}"
            )
    logging.info(f"Msg base: {msgBase1}")
    logging.info(f"Len: {len(msgBase1)}")
    msg = msgBase1

    if len(msg)>280:
        logging.warning("Muy largo")
        return

    if mode == 'test':
        dsts = {
                "twitter": "fernand0Test",
                "telegram": "testFernand0"
               }
    else:
        dsts = {
                "twitter": "botElectrico",
                "telegram": "botElectrico",
                "mastodon": "@botElectrico@botsin.space",
                "blsk": "botElectrico.bsky.social"
                }

    logging.info(f"Destinations: {dsts}")

    imgUrl = ''
    for dst in dsts:
        logging.info(f"Destination: {dst}")
        api = getApi(dst, dsts[dst])

        if hh == timeGraph:
            dateP = str(now).split(' ')[0]
            dateS = str(now + datetime.timedelta(days=1)).split(' ')[0]
            msgTitle = f"Evolución precio para el día {dateS}"
            msgMin = (f"Mínimo a las {minDay[0]}:00 ({minDay[1]:.3f}). ")
            msgMax = (f"Máximo a las {maxDay[0]}:00 ({maxDay[1]:.3f}). ")
            msgAlt = (f"{msgTitle}. {msgMin}\n{msgMax}")
            msgTitle2 = (f"---\n"
                         "layout: post\n"
                         f"title:  '{msgTitle}'\n"
                         f"date:   {dateP} 21:00:59 +0200\n"
                         "categories: jekyll update\n"
                         "---")
            if imgUrl:
                with open(f"{nameGraph[:-4]}.svg", 'r') as f:
                    imageSvg = f.read()
                imageSvg = imageSvg[imageSvg.find('<svg'):]
                posWidth = imageSvg.find("width")
                posViewBox = imageSvg.find("viewBox")
                imageSvg = imageSvg[:posWidth]+imageSvg[posViewBox:]
                imagePlot = ""
                if os.path.exists('/tmp/plotly_graph.html'):
                    with open('/tmp/plotly_graph.html', 'r') as f: 
                        imagePlot = f.read()

                msgMedium = (f"{msgTitle2}\n{msgMin}{msgMax}\n\n"
                             f"{imageSvg}\n"
                             f"{imagePlot}\n"
                             # f"![Gráfica de la evolución del precio para el
                             # día " f"{dateS}]({imgUrl})\n\n"
                             f"\n{table}\n")
            else:
                msgMedium = (f"{msgTitle2}\n{msgMin}{msgMax}\n\n"
                         f"![Gráfica de la evolución del precio para el día "
                         f"{dateS}](url)\n\n"
                         f"\n{table}\n")

            msgTitle = (f"{msgTitle}\n{msgMin}{msgMax}\n")
                         #f"\n{table}\n")
            with open(f"{nameFile(now)}-post.md", 'w') as f:
                      f.write(msgMedium)
            if dst == 'medium':
                res = api.publishImage(msgMedium, nameGraph, alt=msgAlt)
            else:
                try:
                    res = api.publishImage(msgTitle, nameGraph, alt=msgAlt)
                    if hasattr(api, 'lastRes'): 
                        lastRes = api.lastRes
                    else:
                        lastRes = None

                    if (lastRes 
                        and ('media_attachments' in api.lastRes)
                        and (len(api.lastRes['media_attachments']) >0) 
                        and ('url' in api.lastRes['media_attachments'][0])):
                        imgUrl = api.lastRes['media_attachments'][0]['url']
                except:
                    logging.info(f"Fail!")

        if dst != 'medium':
            res = api.publishPost(msg, "", "")
            print(res)

        print(res)

if __name__ == "__main__":
    main()
