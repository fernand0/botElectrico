#!/usr/bin/env python

import datetime
import getpass
import json
import keyring
import logging
import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib.patches as patches
import requests
import sys

from configMod import *

apiBase = "https://apidatos.ree.es/"

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
        # https://pybonacci.org/2020/05/12/demanda-electrica-en-espana-durante-el-confinamiento-covid-19-visto-con-python/
        # https://api.esios.ree.es/
        # https://www.ree.es/es/apidatos
        urlPrecio = (
            f"{apiBase}es/datos/mercados/precios-mercados-tiempo-real?"\
            f'start_date={(now).strftime("%Y-%m-%dT00:00")}'\
            f'&end_date={(now).strftime("%Y-%m-%dT23:59")}'\
            f"&time_trunc=hour"
        )
        data = None
        while not data:
            result = requests.get(urlPrecio)
            data = json.loads(result.content)
            if (('errors' not in data) and 
                (data["included"][0]["attributes"]["title"].find('PVPC')>= 0)):
                    # When the PVPC is not ready the API serves
                    # "Precio mercado spot (\u20ac/MWh)", which 
                    # is the prize paid to producers
                    with open(name, 'w') as f:
                        json.dump(data, f)
            else:
                data = None    
            if not data:
                print("Waiting to see if it is available later")
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

def graficaDia(now, delta):

    nowNext = now + datetime.timedelta(hours=delta)
    data = getData(nowNext)
    # create data
    values=[val['value']/1000 
            for val in data["included"][0]["attributes"]["values"]]

    plt.title(f"Evolución precio para el día {str(nowNext).split(' ')[0]}")

    maxy = 0.275
    miny = 0.010
    plt.ylim((miny, maxy))
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

    arrowprops = dict(arrowstyle='simple', linewidth='0.0001', 
            color='paleturquoise')

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
    return name, minDay, maxDay

def masBarato(data, hours): 
    startH = int(hours[0].split(':')[0])
    endH = int(hours[1].split(':')[0])
    if endH == '00':
        endH = '24'

    print(f"start: {startH}, {endH}")
    # print(data)
    values = data["included"][0]["attributes"]["values"]

    # for val in [values[start*8:(start+1)*8] for start in range(3)]:
    maxV = 0
    minV = 100000
    for hour in values[startH: endH]:
        # print(f"{hour}")
        if hour['value']>maxV:
            maxV = hour['value']
            hourMax = hour
        if hour['value']<minV:
            minV = hour['value']
            hourMin = hour
    print(f"Max {maxV} {hourMax['datetime']}")
    print(f"Min {minV} {hourMin['datetime']}")
    return(hourMin, hourMax)

def main():

    mode = None
    if len(sys.argv) > 1:
        if sys.argv[1] == '-t':
            mode = 'test'

    ranges = {
        "llano1": ["08:00", "10:00"],
        "punta1": ["10:00", "14:00"],
        "llano2": ["14:00", "18:00"],
        "punta2": ["18:00", "22:00"],
        "llano3": ["22:00", "24:00"],
        "valle":  ["00:00", "8:00"]
    }

    button = {"llano": "🟠", "valle": "🟢", "punta": "🔴"}

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    now = datetime.datetime.now()

    if mode == 'test':
        now = convertToDatetime("21:00")
    # print(now)

    dd = now.weekday()
    hh = now.hour
    mm = now.minute

    data = getData(now)
    # Trying to catch errors in obtaining data

    pos = int(hh)
    tipo = data["included"][0]["attributes"]["title"]
    tipo = tipo.replace("M", "k")

    precio = data["included"][0]["attributes"]["values"][pos]["value"]

    if pos < 23:
        prizeNext = data["included"][0]["attributes"]["values"][pos+1]["value"]
    else:
        nextDay = now + datetime.timedelta(hours=1)
        dataNext = getData(nextDay)

        prizeNext = dataNext["included"][0]["attributes"]["values"][0]["value"]

    prize = float(precio) / 1000
    prizeNext = float(prizeNext) / 1000

    franja = "valle"
    luego = ''
    empiezaTramo = False
    minData = None

    if dd > 4:
        hours = ["00:00", "24:00"]
        minData, maxData = masBarato(data, hours)
        start = convertToDatetime(hours[0])
        end = convertToDatetime(hours[1])
    else:
        for hours in ranges:
            start = convertToDatetime(ranges[hours][0])
            end = convertToDatetime(ranges[hours][1])

            if ((start <= now) and (now < end)):
                if hours[-1].isdigit():
                    # llano1, punta1, ....
                    franja = hours[:-1]

                tipoHora = hours
                minData, maxData = masBarato(data, ranges[hours])
                break

    if minData:
        timeMin = int(minData['datetime'].split('T')[1][:2])
        timeMax = int(maxData['datetime'].split('T')[1][:2])

    if hh == start.hour:
        empiezaTramo = True
        msgBase1 = "Empieza"
    else: 
        msgBase1 = "Estamos en"
    msgBase1 = f"{msgBase1} periodo {franja}"

    timeGraph = 21 
    if hh == timeGraph:
        nameGraph, minDay, maxDay = graficaDia(now, 24 - timeGraph)

    if franja == "valle":
        if dd <= 4:
            msgFranja = "(entre las 00:00 y las 8:00)"
        else:
            msgFranja = "(todo el día)"
    else:
        msgFranja = (f"(entre las {ranges[tipoHora][0]} "
                    f"y las {ranges[tipoHora][1]})")

    msgBase1 = f"{msgBase1} {msgFranja}. Precios {tipo}"

    msgPrecio = (
        f"\nEn esta hora: {prize:.3f}"# {tipo}"
        f"\nEn la hora siguiente: "
        f"{prizeNext:.3f}{nextSymbol(prize, prizeNext)}"
        )

    if empiezaTramo:
        prizeMin = float(minData['value'])/1000
        prizeMax = float(maxData['value'])/1000
        msgMaxMin = ( 
                f"\nMín: {prizeMin:.3f}, entre las {timeMin} y "
                f"las {timeMin+1} (hora más económica)" 
                f"\nMáx: {prizeMax:.3f}, entre las {timeMax} y "
                f"las {timeMax+1} (hora más cara)" 
                #f"\nHora más cara entre las {timeMax} y las {timeMax+1}: "
                #f"{prizeMax:.3f}"
                )
        msgBase1 = f"{msgBase1}{msgMaxMin}" 
        #f" Luego baja."
    msgBase1 = (
            f"{button[franja]} {msgBase1}"
            f"{msgPrecio}"
            )
    print(msgBase1)
    print(len(msgBase1))
    msg = msgBase1

    if len(msg)>280:
        print("Muy largo")
        return

    if mode == 'test':
        dsts = {
            "twitter": "fernand0Test",
            "telegram": "testFernand0",
            "facebook": "Fernand0Test",
        }
    else:
        dsts = {
            "twitter": "botElectrico",
            "telegram": "botElectrico",
            "mastodon": "@botElectrico@botsin.space",
            "facebook": "BotElectrico",
        }

    print(dsts)

    for dst in dsts:
        print(dst)
        api = getApi(dst, dsts[dst])
        print(api, dsts[dst])
        res = api.publishPost(msg, "", "")
        print(res)

        if now.hour == timeGraph: 
            dateS = str(now + datetime.timedelta(days=1)).split(' ')[0]
            msgImage = f"Evolución precio para el día {dateS}"
            msgAlt = (f"{msgImage}. Mínimo a las {minDay[0]} ({minDay[1]}. "
                      f"Máximo a las {maxDay[0]} ({maxDay[1]}. "
                      )
            res = api.publishImage(msgImage, nameGraph, alt=msgAlt)
        print(res)


if __name__ == "__main__":
    main()
