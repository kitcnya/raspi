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
