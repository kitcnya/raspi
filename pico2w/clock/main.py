# -*- coding: utf-8-unix -*-
# Copyright (C) 2025 kitcnya@outlook.com
# https://opensource.org/license/mit/
# SPDX-License-Identifier: MIT

import gc
import time
import json
from task import *
from led import *

from logging import basicConfig, WARNING, INFO, DEBUG
logfile = 'main.log'
logformat = '%(asctime)s %(levelname)s: %(message)s'
#basicConfig(filename = logfile, filemode = 'a', format = logformat, level = DEBUG)
basicConfig(filename = logfile, filemode = 'a', format = logformat, level = INFO)
#basicConfig(filename = logfile, filemode = 'a', format = logformat, level = WARNING)

from logging import getLogger
logger = getLogger(__name__)

def main():
    #morse_demo1().run()
    s = sequencer()
    s.led = led()
    op = morse(s)
    op.tone('... - .- .-.- -///') # start
    gc.collect() # force gc
    op.set_time()
    op.task()
    s.run()
    logger.info('led ok')

    try:
        with open('rtc.json') as t:
            st = json.load(t)
        year = st['year']
        month = st['month']
        day = st['day']
        weekday = st['weekday']
        hour = st['hour']
        minute = st['minute']
        second = st['second']
        subsecond = st['subsecond']
        rtc = machine.RTC()
        rtc.datetime((year, month, day, weekday, hour, minute, second, subsecond))
        logger.warning('rtc.json: %d-%02d-%02d %02d:%02d:%02d' % (year, month, day, hour, minute, second))
    except Exception as e:
        logger.error('%s: %s' % (e.__class__.__name__, e.value))

    with open('profile.json') as f:
        profile = json.load(f)

    logger.info(str(profile))

    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(profile['wlan']['ssid'], profile['wlan']['pass'])

    while not wlan.isconnected() and wlan.status() >= 0:
        s.led.on()
        time.sleep(0.2)
        s.led.off()
        time.sleep(0.2)
        s.led.on()
        time.sleep(0.2)
        s.led.off()
        time.sleep(0.2)

    logger.info('wlan connected')
    logger.info(str(wlan.ifconfig()))

    ok = morse(s)
    ok.tone('///--- -.-/...- .-///') # OK VA
    gc.collect() # force gc
    ok.set_time()
    ok.task()
    s.run()

    wlan.disconnect()
    logger.info('wlan disconnected')

logger.warning('starting up')
try:
    main()
    logger.critical('mainloop exit.')
except Exception as e:
    logger.critical('%s: %s' % (e.__class__.__name__, e.value))
