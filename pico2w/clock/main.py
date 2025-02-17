# -*- coding: utf-8-unix -*-
# Copyright (C) 2025 kitcnya@outlook.com
# https://opensource.org/license/mit/
# SPDX-License-Identifier: MIT

import gc
import time
import json
import network
from task import *
from led import *
from nettime import *

from logging import basicConfig, WARNING, INFO, DEBUG
logfile = 'main.log'
logformat = '%(asctime)s %(levelname)s: %(message)s'
#basicConfig(filename = logfile, filemode = 'a', format = logformat, level = DEBUG)
basicConfig(filename = logfile, filemode = 'a', format = logformat, level = INFO)
#basicConfig(filename = logfile, filemode = 'a', format = logformat, level = WARNING)

from logging import getLogger
logger = getLogger(__name__)

def get_profile(s):
    with open('profile.json') as f:
        profile = json.load(f)
    logger.info(str(profile))
    try:
        tz = profile['tz']
    except:
        tz = dict()
        profile['tz'] = tz
    seconds = 0
    try:
        tmp = int(tz['hours'])
        seconds = tmp * 3600
    except:
        pass
    try:
        tmp = int(tz['minutes'])
        seconds = tmp * 60
    except:
        pass
    try:
        tmp = int(tz['seconds'])
        seconds = tmp
    except:
        pass
    profile['tz']['seconds'] = seconds
    logger.info('timezone: %s seconds' % seconds)
    return profile

def rtc_set(epoch): # localtime
    (year, month, day, hour, minute, second, weekday, yearday) = time.gmtime(epoch)
    rtc = machine.RTC()
    rtc.datetime((year, month, day, 0, hour, minute, second, 0))
    logger.warning('rtc: %d-%02d-%02d %02d:%02d:%02d' % (year, month, day, hour, minute, second))

def rtc_json(s):
    try:
        with open('rtc.json') as t:
            st = json.load(t)
        epoch = st['epoch']
        epoch += s.profile['tz']['seconds']
        rtc_set(epoch + 1) # XXX: w/ adjust
    except Exception as e:
        logger.error('%s: %s (rtc.json)' % (e.__class__.__name__, e.value))

def greeting(s):
    op = morse(s)
    op.tone('... - .- .-.- -///') # start
    op.set_time()
    op.task()
    s.run()

def wlan_init(s):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(s.profile['wlan']['ssid'], s.profile['wlan']['pass'])
    # connect would processed in the background...
    timeout = time.time() + int(s.profile['wlan']['timeout'])
    while True:
        iscn = wlan.isconnected()
        stat = wlan.status()
        if iscn and stat == network.STAT_GOT_IP:
            break
        if time.time() > timeout:
            raise RuntimeError('WLAN not available; last status = %s', stat)
        s.led.on()
        time.sleep(0.2)
        s.led.off()
        time.sleep(0.2)
    logger.info('wlan connected')
    logger.info(str(wlan.ifconfig()))
    return wlan

def ntp_init(s):
    server = s.profile['ntp']['server']
    servers = s.profile['ntp']['servers']
    index = s.profile['ntp']['index']
    offset = s.profile['ntp']['offset']
    timeout = s.profile['ntp']['timeout']
    timezone = s.profile['tz']['seconds']
    ntp = nettime(server, servers, index, offset, timeout, timezone)
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
    logger.info('initial ntp server: %s' % str(ntp.ntpserver))
    return ntp, epoch, ticks

class ntptask(task):

    def init(self):
        #self.warn_cputime = 700000 # report long task over this
        self.faults = 0

    def task(self):
        try:
            (epoch, ticks) = self.sequencer.ntp.get()
        except Exception as e:
            logger.error('%s: %s (ntp.get)' % (e.__class__.__name__, e.value))
            epoch = 0
        if epoch == 0:
            self.faults += 1
            if self.faults >= 10:
                raise RuntimeError('no response from ntp server')
        else:
            self.faults = 0
            if epoch != self.sequencer.clock.epoch:
                #logger.warning('epoch: %s (internal) != %s (ntp)' % (self.sequencer.clock.epoch, epoch))
                d = epoch - self.sequencer.clock.epoch
                self.sequencer.clock.epoch = epoch
                self.sequencer.clock.ticks = time.ticks_add(self.sequencer.clock.ticks, d * 1000000)
            d = time.ticks_diff(self.sequencer.clock.ticks, ticks)
            logger.warning('ticks: %s (internal - ntp) %s' % (d, str(self.sequencer.ntp.ntpserver)))
            self.sequencer.clock.set_time(ticks)
        self.sequencer.clock.epoch += 1
        self.sequencer.clock.set_alarm(self.sequencer.clock, 1000000)

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
        if second % 10 == 0:
            self.off.set_alarm(self, 100000)
            self.on2.set_alarm(self, 200000)
            self.off2.set_alarm(self, 300000)
        else:
            self.off.set_alarm(self, 150000)
            if second == 2 and minute % 10 == 2:
                self.ticks = self._alarm
                self.ntp.set_alarm(self, 160000)
                return
            elif second % 10 == 8:
                gc.collect()
        self.epoch += 1
        self.set_alarm(self, 1000000)

def main():
    s = sequencer()
    s.led = led()
    s.clock = clock(s)
    s.profile = get_profile(s)
    rtc_json(s)
    greeting(s)
    wlan = wlan_init(s)
    (s.ntp, s.clock.epoch, s.clock.ticks) = ntp_init(s)

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
