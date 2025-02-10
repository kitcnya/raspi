# -*- coding: utf-8-unix -*-
# Copyright (C) 2025 kitcnya@outlook.com
# https://opensource.org/license/mit/
# SPDX-License-Identifier: MIT

import time
import machine
from task import *

from logging import getLogger
logger = getLogger(__name__)

class led(object):

    def __init__(self):
        self.led = machine.Pin("LED", machine.Pin.OUT)

    def on(self):
        self.led.value(1)

    def off(self):
        self.led.value(0)

class led_on(task):

    def task(self):
        self.sequencer.led.on()

class led_off(task):

    def task(self):
        self.sequencer.led.off()

class morse(task):

    def init(self):
        self.codes = list()
        self.next = 10000 # first delay
        self.unit = 100000
        self.unit_long = self.unit * 3
        self.unit_cspace = self.unit * 3
        self.unit_wspace = self.unit * 7

    def tone(self, s):
        for t in s:
            if t == '.':
                self.codes.append((led_on(self.sequencer), self.next))
                self.next += self.unit
                self.codes.append((led_off(self.sequencer), self.next))
                self.next += self.unit
            elif t == '-':
                self.codes.append((led_on(self.sequencer), self.next))
                self.next += self.unit_long
                self.codes.append((led_off(self.sequencer), self.next))
                self.next += self.unit
            elif t == ' ':
                self.next += self.unit_cspace
            elif t == '/':
                self.next += self.unit_wspace
            elif t == '=':
                self.codes.append((self, self.next))

    def task(self):
        for obj, next in self.codes:
            obj.set_alarm(self, next)
