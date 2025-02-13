# -*- coding: utf-8-unix -*-
# Copyright (C) 2025 kitcnya@outlook.com
# https://opensource.org/license/mit/
# SPDX-License-Identifier: MIT

import gc
import time
import json
import socket as so
import struct
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

class ntpget(object):

    def __init__(self, server):
        self.server = server
        self.ntpserver = so.getaddrinfo(self.server, 123)[0][-1]
        self.sock = so.socket(so.AF_INET, so.SOCK_DGRAM, 0)
        self.sock.settimeout(0.5)
        self.request = b'\x23' + 47 * b'\0'

    def get(self):
        start = time.ticks_us()
        self.sock.sendto(self.request, self.ntpserver)
        try:
            answer, src = self.sock.recvfrom(64)
        except Exception as e:
            logger.error('%s: %s' % (e.__class__.__name__, e.value))
            return start, 0, 0
        end = time.ticks_us()
        data = struct.unpack('!12I', answer)
        ntptime = data[10] # transmit timestamp (sec) on server
        if ntptime < 2147483648:
            ntptime += 2147483648 # ntp era 1 (beyond 7-Feb-2036 06:28:16)
        else:
            ntptime -= 2147483648 # ntp era 0 (since 20-Jan-1968 03:14:08)
        epoch = ntptime - 61505152
        ticks = time.ticks_add(start, time.ticks_diff(end, start) // 2)
        return ticks, epoch, data[11]

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

    ntp = ntpget(profile['ntp']['server'])

    ok = morse(s)
    ok.tone('///--- -.-/...- .-///') # OK VA

    while True:
        gc.collect() # force gc
        op.set_time()
        op.task()
        s.run()

        logger.info('start: %s' % (time.ticks_ms()))

        (ticks, epoch, frac) = ntp.get()
        if epoch != 0:
            epoch += 9 * 3600 # UTC->JST
            (year, month, mday, hour, minute, second, weekday, yearday) = time.gmtime(epoch)
            logger.info('ntptime: %d-%02d-%02d %02d:%02d:%02d' % (year, month, mday, hour, minute, second))

            logger.info('rtc set: %s' % (time.ticks_ms()))

            rtc.datetime((year, month, mday, 0, hour, minute, second, 0))
            (year, month, day, weekday, hour, minute, second, subsecond) = rtc.datetime()
            logger.info('rtc: %d-%02d-%02d %02d:%02d:%02d' % (year, month, day, hour, minute, second))

            logger.info('end: %s' % (time.ticks_ms()))

        gc.collect() # force gc
        ok.set_time()
        ok.task()
        s.run()
        time.sleep(600)

    wlan.disconnect()
    logger.info('wlan disconnected')

logger.warning('starting up')
try:
    main()
    logger.critical('mainloop exit.')
except Exception as e:
    logger.critical('%s: %s' % (e.__class__.__name__, e.value))
