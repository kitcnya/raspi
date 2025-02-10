# -*- coding: utf-8-unix -*-
# Copyright (C) 2025 kitcnya@outlook.com
# https://opensource.org/license/mit/
# SPDX-License-Identifier: MIT

import time
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

class main(sequencer):

    def init(self):
        self.led = led()
        self.led.on()
        off = led_off(self)
        off.set_alarm(off, 5000000)
        msg = morse(self)
        msg.set_alarm(msg, 6000000)
        #         k   i  t c    n  y    a  1
        msg.tone('-.- .. - -.-. -. -.-- .-/.----///=')
        #msg.tone('...,---,...///=')
        logger.info('msg length: %s' % msg.next)

logger.warning('starting up')
try:
    main().run()
    logger.critical('mainloop exit.')
except Exception as e:
    logger.critical('%s: %s' % (e.__class__.__name__, e.value))
