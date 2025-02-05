# -*- coding: utf-8-unix -*-
import os
import sys
import machine, time

from logging import basicConfig, WARNING, INFO, DEBUG
logfile = 'main.log'
logformat = '%(asctime)s %(levelname)7s: %(message)s'
#basicConfig(filename = logfile, filemode = 'w', format = logformat, level = DEBUG)
basicConfig(filename = logfile, filemode = 'w', format = logformat, level = INFO)
#basicConfig(filename = logfile, filemode = 'w', format = logformat, level = WARNING)

from logging import getLogger
logger = getLogger(__name__)

logger.warning('starting up')

class task(object):
    def __init__(self, interval = 0):
        self._interval = interval
        self.record_start()
        self.record_end()
        self._alarm = self._start # force interval zero
    def invoke(self):
        self.record_start()
        self._invoke()
        self._end = time.ticks_us()
    def record_start(self):
        self._start = time.ticks_us()
        self.set_alarm(self, self._interval)
    def record_end(self):
        self._end = time.ticks_us()
        self._cputime = time.ticks_diff(self._end, self._start)
    def set_alarm(self, task, after):
        self._alarm = time.ticks_add(task._start, after)
    def _invoke(self):
        pass

class mainloop(object):
    def __init__(self):
        self.tasks = list()
    def append(self, task):
        self.tasks.append(task)
        logger.info('task: %s' % task.__class__.__name__)
    def run(self):
        while True:
            self.dispatch()
    def dispatch(self):
        now = time.ticks_us()
        for task in self.tasks:
            if time.ticks_diff(now, task._alarm) < 0:
                continue
            task.invoke()
            logger.debug('cputime: %s %s' % (task.__class__.__name__, task._cputime))

led = machine.Pin("LED", machine.Pin.OUT)

class led_on(task):
    def __init__(self):
        super().__init__(1000000)
    def _invoke(self):
        led.value(1)

class led_off(task):
    def __init__(self):
        super().__init__(1000000)
    def _invoke(self):
        led.value(0)

class main(mainloop):
    def __init__(self):
        super().__init__()
        self.on = led_on()
        self.off = led_off()
        self.append(self.on)
        self.append(self.off)
        self.off.set_alarm(self.on, 200000)

try:
    main().run()
except Exception as e:
    logger.error('%s: %s' % (e.__class__.__name__, e.value))
