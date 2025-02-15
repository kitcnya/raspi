# -*- coding: utf-8-unix -*-
# Copyright (C) 2025 kitcnya@outlook.com
# https://opensource.org/license/mit/
# SPDX-License-Identifier: MIT

import gc
import time
import json
import socket as so
import struct
import network
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

    def __init__(self, server, timeout = 0.5):
        self.ntpserver = so.getaddrinfo(server, 123)[0][-1]
        self.timeout = timeout
        self.request = b'\x23' + 47 * b'\0'

    def get(self):
        sock = so.socket(so.AF_INET, so.SOCK_DGRAM, 0)
        sock.settimeout(self.timeout)
        start = time.ticks_us()
        try:
            sock.sendto(self.request, self.ntpserver)
            answer, src = sock.recvfrom(64)
        except Exception as e:
            logger.error('%s: %s (timeout?)' % (e.__class__.__name__, e.value))
            sock.close()
            return 0, start
        end = time.ticks_us()
        sock.close()
        data = struct.unpack('!12I', answer)
        ntptime = data[10] # transmit timestamp (sec) on server
        if ntptime < 2147483648:
            ntptime += 2147483648 # ntp era 1 (beyond 7-Feb-2036 06:28:16)
        else:
            ntptime -= 2147483648 # ntp era 0 (since 20-Jan-1968 03:14:08)
        epoch = ntptime - 61505152
        usec = data[11] // 4295 # convert transmit timestamp (frac) on server into usec
        ticks = time.ticks_add(start, (time.ticks_diff(end, start) // 2) - usec)
        epoch += 9 * 3600 # UTC->JST
        return epoch, ticks

def rtc_set(epoch): # localtime
    (year, month, day, hour, minute, second, weekday, yearday) = time.gmtime(epoch)
    rtc = machine.RTC()
    rtc.datetime((year, month, day, 0, hour, minute, second, 0))
    logger.warning('rtc: %d-%02d-%02d %02d:%02d:%02d' % (year, month, day, hour, minute, second))

def rtc_json():
    try:
        with open('rtc.json') as t:
            st = json.load(t)
        epoch = st['epoch']
        epoch += 9 * 3600 # UTC->JST
        rtc_set(epoch + 1) # XXX: w/ adjust
    except Exception as e:
        logger.error('%s: %s (rtc.json)' % (e.__class__.__name__, e.value))

def greeting(s):
    op = morse(s)
    op.tone('... - .- .-.- -///') # start
    op.set_time()
    op.task()
    s.run()

def get_profile(s):
    with open('profile.json') as f:
        profile = json.load(f)
    logger.info(str(profile))
    return profile

def wlan_init(s, profile):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(profile['wlan']['ssid'], profile['wlan']['pass'])
    # connect would processed in the background...
    while not wlan.isconnected() and wlan.status() >= 0:
        s.led.on()
        time.sleep(0.2)
        s.led.off()
        time.sleep(0.2)
    logger.info('wlan connected')
    logger.info(str(wlan.ifconfig()))
    return wlan

def ntp_init(s, profile):
    w1 = morse(s)
    w1.tone('-. ---/-. - .--./... . .-. ...- . .-.///') # no ntp server
    n = 0
    try:
        ntp = ntpget(profile['ntp']['server'], profile['ntp']['timeout'])
    except Exception as e:
        logger.error('%s: %s (ntp)' % (e.__class__.__name__, e.value))
        ntp = None
    while ntp is None:
        n += 1
        if n >= 10:
            raise RuntimeError('no ntp server')
        gc.collect()
        w1.set_time()
        w1.task()
        s.run()
        try:
            ntp = ntpget(profile['ntp']['server'], profile['ntp']['timeout'])
        except Exception as e:
            logger.error('%s: %s (ntp)' % (e.__class__.__name__, e.value))
            ntp = None
    w2 = morse(s)
    w2.tone('-. - .--./--. . -/- .. -- .///') # ntp get time
    n = 0
    try:
        (epoch, ticks) = ntp.get()
    except Exception as e:
        logger.error('%s: %s (ntp.get)' % (e.__class__.__name__, e.value))
        epoch = 0
    while epoch == 0:
        n += 1
        if n >= 10:
            raise RuntimeError('no response from ntp server')
        gc.collect()
        w2.set_time()
        w2.task()
        s.run()
        try:
            (epoch, ticks) = ntp.get()
        except Exception as e:
            logger.error('%s: %s (ntp.get)' % (e.__class__.__name__, e.value))
            epoch = 0
    rtc_set(epoch + 1) # XXX: w/ adjust
    return ntp, epoch, ticks

class ntptask(task):

    def task(self):
        try:
            (epoch, ticks) = self.sequencer.ntp.get()
        except Exception as e:
            logger.error('%s: %s (ntp.get)' % (e.__class__.__name__, e.value))
            epoch = 0
        if epoch == 0: return
        epoch += 1
        if epoch != self.sequencer.clock.epoch:
            logger.warning('epoch: %s (internal) != %s (ntp)' % (self.sequencer.clock.epoch, epoch))
            self.sequencer.clock.epoch = epoch
        d = time.ticks_diff(ticks, self.sequencer.clock.ticks)
        logger.warning('ticks: %s (internal - ntp)' % d)
        self.sequencer.clock.set_time(ticks, 1000000)

class clock(task):

    def init(self):
        self.ntp = ntptask(self.sequencer)
        self.off = led_off(self.sequencer)
        self.on2 = led_on(self.sequencer)
        self.off2 = led_off(self.sequencer)

    def setup(self):
        self.epoch += 2
        self.set_time(self.ticks)
        self.set_alarm(self, 2000000)
        logger.info('clock will start afater two seconds.')

    def task(self):
        self.sequencer.led.on()
        (year, month, day, hour, minute, second, weekday, yearday) = time.gmtime(self.epoch)
        if second == 0:
            self.off.set_alarm(self, 100000)
            self.on2.set_alarm(self, 200000)
            self.off2.set_alarm(self, 300000)
        else:
            self.off.set_alarm(self, 150000)
            if second == 2 and minute % 10 == 2:
                self.ticks = self._alarm
                self.ntp.set_alarm(self, 160000)
            elif second == 59:
                gc.collect()
        self.epoch += 1
        self.set_alarm(self, 1000000)

def main():
    rtc_json()
    s = sequencer()
    s.led = led()
    s.clock = clock(s)
    greeting(s)
    profile = get_profile(s)
    wlan = wlan_init(s, profile)
    (s.ntp, s.clock.epoch, s.clock.ticks) = ntp_init(s, profile)

    s.clock.setup()
    s.run()

    wlan.disconnect()
    logger.info('wlan disconnected')

logger.warning('starting up')
try:
    main()
    logger.critical('mainloop exit.')
except Exception as e:
    logger.critical('%s: %s.' % (e.__class__.__name__, e.value))
led().on()
