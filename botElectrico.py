#!/usr/bin/env python

import datetime
import getpass
import json
import keyring
import logging
import sys
import time
import requests

import moduleTwitter
from configMod import *

def getPassword(server, user):
    # Para borrar keyring.delete_password(server, user)
    password = keyring.get_password(server, user)
    if not password:
        logging.info("[%s,%s] New account. Setting password" % (server, user))
        password = getpass.getpass()
        keyring.set_password(server, user, password)
    return password

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
    apiBase ='https://apidatos.ree.es/'
    urlPrecio = (f'{apiBase}es/datos/mercados/precios-mercados-tiempo-real?'
                 f'start_date={(now-delta).strftime("%Y-%m-%dT%H:%M")}'
                 f'&end_date={(now).strftime("%Y-%m-%dT%H:%M")}'
                 '&time_trunc=hour')
    token = getPassword(apiBase, 'fernand0@elmundoesimperfecto.com')
    headers = {"Authorization": f'Token token="{token}"'}

    # https://pybonacci.org/2020/05/12/demanda-electrica-en-espana-durante-el-confinamiento-covid-19-visto-con-python/
    # https://api.esios.ree.es/
    # https://www.ree.es/es/apidatos

    ses = requests.Session()
    ses.headers.update(headers)
    # print(ses.headers)
    # print(ses.headers['Authorization'])
    result = ses.get(urlPrecio, headers=headers)
    data = json.loads(result.content)
    # print(result.headers)
    # return

    tipo = data['included'][0]['attributes']['title']
    precio = data['included'][0]['attributes']['values'][0]['value']

    hh = now.hour
    mm = now.minute
    msgBase = f"Son las {hh:0>2}:{mm:0>2} "\
              f" y estamos en hora valle."\
              f"\n         Precio: {precio} ({tipo})."\
              f"\n         Esta franja "
    franja = 'valle'
    for hours in ranges:
        #start = ranges[hours][0]
        #start = datetime.datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
        start = convertToDatetime(ranges[hours][0])
        end = convertToDatetime(ranges[hours][1])

        if (now.weekday()<=4) and ((start <= now) and (now < end)):
            tipoHora = hours
            if tipoHora[-1].isdigit(): 
                tipoHora = tipoHora[:-1]
            franja = hours

    if franja == 'valle':
        if now.weekday()<=4:
            msgFranja = 'va desde las 00:00 hasta las 8:00'
        else:
            msgFranja = 'dura todo el fin de semana'
    else:
        msgFranja = 'va desde {ranges[franja][0]} hasta {ranges[franja][1]}'

    msg = f'{button[franja]} {msgBase} {msgFranja}'
    print(msg)

    dsts = {'twitter':'botElectrico',
            'telegram':'botElectrico',
            'mastodon':'@botElectrico@botsin.space'}

    for dst in dsts:
        print(dst)
        api = getApi(dst, dsts[dst])
        print(api, dsts[dst])
        res = api.publishPost(msg,"","")
        print(res)


if __name__ == "__main__":
    main()
