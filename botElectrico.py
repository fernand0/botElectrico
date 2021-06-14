#!/usr/bin/env python

import datetime
import getpass
import json
import keyring
import logging
import matplotlib.pyplot as plt
import matplotlib.ticker
import requests
import sys

from configMod import *

apiBase = "https://apidatos.ree.es/"

def nameFile(now):
    return f"/tmp/{now.year}-{now.month:0>2}-{now.day:0>2}"

def getData(now):
    print(now)
    name = f"{nameFile(now)}_data.json"
    print(name)
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
        result = requests.get(urlPrecio)
        data = json.loads(result.content)
        with open(name, 'w') as f:
            json.dump(data, f)

    return data

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

def graficaDia(data, now):

    # create data
    values=[val['value']/1000 
            for val in data["included"][0]["attributes"]["values"]]

    plt.title(f"Evolución precio para el día {str(now).split(' ')[0]}")

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

    # plt.text(0.3, .115, f'Min: {ymin:.3f} ({xmin}:00)')
    # plt.text(0, .114, f'Max: {ymax:.3f} ({xmax}:00)')

    plt.annotate(f'Max: {ymax:.3f} ({xmax}:00)', xy=(xmax,ymax), 
            xytext=(xmax-8,ymax), arrowprops=dict(arrowstyle='simple'))
    plt.annotate(f'Min: {ymin:.3f} ({xmin}:00)', xy=(xmin,ymin), 
            xytext=(xmin-8,ymin-1/1000), arrowprops=dict(arrowstyle='simple'))
    # plt.axhline(y=ymax, linestyle='dotted')
    # plt.axhline(y=ymin, linestyle='dotted')
    # plt.axvline(x=xmax, linestyle='dotted')
    # plt.axvline(x=xmin, linestyle='dotted')
    # use the plot function
    plt.plot(values)
    #ax.annotate('local max', xy=(xmax, ymax), xytext=(xmax, ymax+5),
    #                    arrowprops=dict(facecolor='black', shrink=0.05),
    #                                )
    plt.show()
    name = f"{nameFile(now)}_image.png"
    plt.savefig(name)

def masBarato(data, hours): 
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
    for hour in values[startH: endH]:
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
        "llano3": ["22:00", "24:00"],
        "valle": ["00:00", "8:00"]
    }

    button = {"llano": "🟠", "valle": "🟢", "punta": "🔴"}

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    now = datetime.datetime.now()
    # print(f'{now.strftime("%Y-%m-%dT%H:%M")}') now = "2021-06-10 14:17:30.993728"
    #now = convertToDatetime("00:01")

    data = getData(now)
    # graficaDia(data, now)

    pos = int(now.hour)
    tipo = data["included"][0]["attributes"]["title"]
    precio = data["included"][0]["attributes"]["values"][pos]["value"]
    if pos < 23:
        precioSig = data["included"][0]["attributes"]["values"][pos+1]["value"]
    else:
        nowSig = now + datetime.timedelta(hours=1)
        dataSig = getData(nowSig)
        precioSig = dataSig["included"][0]["attributes"]["values"][0]["value"]
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
    minData = None
    for hours in ranges:
        start = convertToDatetime(ranges[hours][0])
        end = convertToDatetime(ranges[hours][1])
        print(f"{start}")
        print(f"{end}")

        if (now.weekday() <= 4) and ((start <= now) and (now < end)):
            if hours[-1].isdigit():
                franja = hours[:-1]
            else:
                franja = hours

            tipoHora = hours

            minData, maxData = masBarato(data, ranges[hours])
        elif now.weekday() > 4:
            minData, maxData = masBarato(data, ["00:00", "24:00"])

        if minData:
            timeMin = int(minData['datetime'].split('T')[1][:2])
            timeMax = int(maxData['datetime'].split('T')[1][:2])

        if now.hour == start.hour:
                empiezaTramo = True
                msgBase = f"{msgBase} y empieza el periodo {franja}"
                msgBase1 = "Empieza"
        else: 
                msgBase = f"{msgBase} y estamos en periodo {franja}"
                msgBase1 = "Estamos en"
        msgBase1 = f"{msgBase1} periodo {franja}"


    if now.hour == 0:
        graficaDia(data,now)
    # print(now)
    # print(now.hour)
    # return

    if franja == "valle":
        if now.weekday() <= 4:
            msgFranja = "(entre las 00:00 y las 8:00)"
        else:
            msgFranja = "(todo el día)"
    else:
        msgFranja = (f"(entre las {ranges[tipoHora][0]} "
                    f"y las {ranges[tipoHora][1]})")

    msgBase1 = f"{msgBase1} {msgFranja}. Precios {tipo}"

    msgPrecio = (
        f"\nEn esta hora: {precio:.3f}"# {tipo}"
        f"\nEn la hora siguiente: {precioSig:.3f}{sigSymbol}"
        )

    msgBase = (
        f"{msgBase}"
        f"{msgPrecio}"
        f"\nFranja {msgFranja}")

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
        msgBase = f"{msgBase}{msgMaxMin}" 
        msgBase1 = f"{msgBase1}{msgMaxMin}" 
        #f" Luego baja."
    msg = f"{button[franja]} {msgBase}"
    msgBase1 = (
            f"{button[franja]} {msgBase1}"
            f"{msgPrecio}"
            )
    print(msg)
    print(len(msg))
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
        }

    print(dsts)

    for dst in dsts:
        print(dst)
        api = getApi(dst, dsts[dst])
        print(api, dsts[dst])
        res = api.publishPost(msg, "", "")
        print(res)

        if now.hour == 0: 
            res = api.publishImage(f"Evolución precio para el día "\
                                   f"{str(now).split(' ')[0]}", 
                                   f"{nameFile(now)}_image.png"
                                  )
        print(res)


if __name__ == "__main__":
    main()
