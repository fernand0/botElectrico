#!/usr/bin/env python

import datetime
import getpass
import json
import keyring
import logging
import requests
import sys

from configMod import *

apiBase = "https://apidatos.ree.es/"

def convertToDatetime(myTime):
    now = datetime.datetime.now()
    date = datetime.datetime.date(now)
    converted = myTime
    converted = datetime.datetime.strptime(f"{date} {converted}",
                                           "%Y-%m-%d %H:%M")

    return converted

def masBarato(hours): 
    now = datetime.datetime.now()
    urlPrecio = (
        f"{apiBase}es/datos/mercados/precios-mercados-tiempo-real?"\
        f'start_date={(now).strftime("%Y-%m-%dT00:00")}'\
        f'&end_date={(now).strftime("%Y-%m-%dT23:59")}'\
        f"&time_trunc=hour"
    )
    result = requests.get(urlPrecio)
    data = json.loads(result.content)

    startH = int(hours[0].split(':')[0])
    endH = int(hours[1].split(':')[0])
    if endH == '00':
        endH = '24'

    # print(data)
    values = data["included"][0]["attributes"]["values"]

    # print(startH, endH)
    # for val in [values[start*8:(start+1)*8] for start in range(3)]:
    maxV = 0
    minV = 100000
    for hour in values[startH: endH+1]:
        print(hour)
        print(f"{hour}")
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
        "llano3": ["22:00", "23:59"],
    }

    button = {"llano": "🟠", "valle": "🟢", "punta": "🔴"}

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    now = datetime.datetime.now()
    # print(f'{now.strftime("%Y-%m-%dT%H:%M")}')
    delta = datetime.timedelta(hours=1, minutes=00)
    urlPrecio = (
        f"{apiBase}es/datos/mercados/precios-mercados-tiempo-real?"
        f'start_date={(now-delta).strftime("%Y-%m-%dT%H:%M")}'
        f'&end_date={(now+delta).strftime("%Y-%m-%dT%H:%M")}'
        "&time_trunc=hour"
    )
    # https://pybonacci.org/2020/05/12/demanda-electrica-en-espana-durante-el-confinamiento-covid-19-visto-con-python/
    # https://api.esios.ree.es/
    # https://www.ree.es/es/apidatos

    ses = requests.Session()
    result = ses.get(urlPrecio)
    data = json.loads(result.content)

    tipo = data["included"][0]["attributes"]["title"]
    precio = data["included"][0]["attributes"]["values"][0]["value"]
    precioSig = data["included"][0]["attributes"]["values"][1]["value"]
    precio = float(precio) / 1000
    precioSig = float(precioSig) / 1000
    tipo = tipo.replace("M", "k")
    if precioSig > precio:
        sigSymbol = "↗"
    elif precioSig < precio:
        sigSymbol = "↘"
    else:
        sigSymbol = "↔"

    hh = now.hour
    mm = now.minute

    franja = "valle"
    msgBase = f"Son las {hh:0>2}:{mm:0>2} "
    luego = ''
    empiezaTramo = False
    for hours in ranges:
        start = convertToDatetime(ranges[hours][0])
        end = convertToDatetime(ranges[hours][1])

        if (now.weekday() <= 4) and ((start <= now) and (now < end)):
            if hours[-1].isdigit():
                franja = hours[:-1]
            else:
                franja = hours

            tipoHora = hours

            if now.hour == start.hour:
                empiezaTramo = True
                msgBase = f"{msgBase} y empieza el periodo {franja}"
            else: 
                empiezaTramo = False
                msgBase = f"{msgBase} y estamos en periodo {franja}"

            minData, maxData = masBarato(ranges[hours])
            timeMin = int(minData['datetime'].split('T')[1][:2])
            timeMax = int(maxData['datetime'].split('T')[1][:2])


    if franja == "valle":
        if now.weekday() <= 4:
            msgFranja = "entre las 00:00 y las 8:00"
        else:
            msgFranja = "dura todo el fin de semana"
    else:
        msgFranja = (f"entre las {ranges[tipoHora][0]} "
                    f"y las {ranges[tipoHora][1]}")

    msgBase = (
        f"{msgBase}"
        f"\n    Precio: {precio:.3f} {tipo}"
        f"\n    En la hora siguiente el precio será: "
        f"{precioSig:.3f}{sigSymbol}"
        f"\nFranja {msgFranja}")

    if empiezaTramo:
        prizeMin = float(minData['value'])/1000
        prizeMax = float(maxData['value'])/1000
        msgBase = (
        f"{msgBase}" 
        f"\nHora más económica "
        f"entre las {timeMin} y las {timeMin+1} ({prizeMin:.3f})"
        f"\nLa más cara entre las {timeMax} y las {timeMax+1} ({prizeMax:.3f})"
        #f" Luego baja."
    )
    msg = f"{button[franja]} {msgBase}"
    print(msg)
    print(len(msg))

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
        }

    print(dsts)

    for dst in dsts:
        print(dst)
        api = getApi(dst, dsts[dst])
        print(api, dsts[dst])
        res = api.publishPost(msg, "", "")
        print(res)


if __name__ == "__main__":
    main()
