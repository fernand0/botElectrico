#!/usr/bin/env python

import datetime
import logging
import sys
import time

import moduleTwitter

def convertToDatetime(myTime):
    now = datetime.datetime.now()
    date = datetime.datetime.date(now)
    converted = myTime
    converted = datetime.datetime.strptime(f"{date} {converted}", "%Y-%m-%d %H:%M")

    return converted

def main():

    ranges = {'punta': ["10:00","14:00"],
              'llana1': ["8:00", "10:00"],
              'llana2': ["14:00", "18:00"],
              'llana3': ["22:00","0:0"]}

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(message)s"
    )

    msg = "Estamos en hora valle [00:00 - 8:00]"
    now = datetime.datetime.now()
    for hours in ranges:
        #start = ranges[hours][0]
        #start = datetime.datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
        start = convertToDatetime(ranges[hours][0])
        end = convertToDatetime(ranges[hours][1])

        if (now >= start) and (now <= end):
            hh = now.hour
            mm = now.minute
            msg = (f"Son las {hh}:{mm} y estamos en hora {hours} {ranges[hours]}")

    print (msg)

    tw = moduleTwitter.moduleTwitter()
    tw.setClient("botElectrico")
    res = tw.publishPost(msg,"","")
    # print(res)


if __name__ == "__main__":
    main()
