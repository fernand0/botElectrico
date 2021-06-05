#!/usr/bin/env python

import datetime
import json
import logging
import sys
import time
import urllib.request

import moduleTwitter

def convertToDatetime(myTime):
    now = datetime.datetime.now()
    date = datetime.datetime.date(now)
    converted = myTime
    converted = datetime.datetime.strptime(f"{date} {converted}", "%Y-%m-%d %H:%M")

    return converted

def main():

    ranges = {'llana1': [ "8:00", "10:00"], 
              'punta1': ["10:00", "14:00"],
              'llana1': ["14:00", "18:00"],
              'punta2': ["18:00", "22:00"],
              'llana3': ["22:00", "23:59"]}

    button = {'llana': '🟠',
              'valle': '🟢',
              'punta': '🔴'}



    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    now = datetime.datetime.now()
    print(f'{now.strftime("%Y-%m-%dT%H:%M")}')
    delta = datetime.timedelta(hours=1, minutes=00)
    urlPrecio = ('https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real?'
     f'start_date={(now-delta).strftime("%Y-%m-%dT%H:%M")}'
     f'&end_date={(now).strftime("%Y-%m-%dT%H:%M")}'
     '&time_trunc=hour')
    # https://pybonacci.org/2020/05/12/demanda-electrica-en-espana-durante-el-confinamiento-covid-19-visto-con-python/
    # https://www.ree.es/es/apidatos


    data = json.loads(urllib.request.urlopen(urlPrecio).read())

    tipo = data['included'][0]['attributes']['title']
    precio = data['included'][0]['attributes']['values'][0]['value']

    hh = now.hour
    mm = now.minute
    msg = f"{button['valle']} Son las {hh:0>2}:{mm:0>2} "\
          f" y estamos en hora valle [00:00 - 8:00]."\
          f"\n         Precio: {precio} ({tipo})."
    for hours in ranges:
        #start = ranges[hours][0]
        #start = datetime.datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
        start = convertToDatetime(ranges[hours][0])
        end = convertToDatetime(ranges[hours][1])

        if (now.weekday()<=4) and ((start <= now) and (now < end)):
            tipoHora = hours
            if tipoHora[-1].isdigit(): 
                tipoHora = tipoHora[:-1]
            msg = (f"{button[tipoHora]} Son las {hh:0>2}:{mm:0>2} "\
                   f"y estamos en hora {tipoHora} {ranges[hours]}"\
                   f"\n         Precio: {precio} ({tipo}).")
        else:
            print("no")

    tw = moduleTwitter.moduleTwitter()
    tw.setClient("botElectrico")
    res = tw.publishPost(msg,"","")
    # print(res)


if __name__ == "__main__":
    main()
