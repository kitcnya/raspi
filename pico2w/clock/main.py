# -*- coding: utf-8-unix -*-
import os
import sys
import math
import time
import machine

from logging import basicConfig, WARNING, INFO, DEBUG
logfile = 'main.log'
logformat = '%(asctime)s %(levelname)7s: %(message)s'
#basicConfig(filename = logfile, filemode = 'a', format = logformat, level = DEBUG)
basicConfig(filename = logfile, filemode = 'a', format = logformat, level = INFO)
#basicConfig(filename = logfile, filemode = 'a', format = logformat, level = WARNING)

from logging import getLogger
logger = getLogger(__name__)

logger.warning('starting up')

class task(object):
    measures = 100
    measures1 = measures - 1
    taskid = 0
    def __init__(self, main):
        self._main = main
        self._start = main.start
        self._end = main.start
        self._alarm = main.start
        self._cputime = 0
        self._cputime_mean = 0
        self._cputime_mean_square = 0
        self._cputime_m = 0
        self._taskid = task.taskid
        task.taskid += 1
    def invoke(self):
        self._start = self._main.ticks()
        self._invoke()
        self._end = self._main.ticks()
        self._cputime = time.ticks_diff(self._end, self._start)
        self._cputime_mean = (self._cputime_mean * task.measures1 + self._cputime) / task.measures
        self._cputime_mean_square = (self._cputime_mean_square * task.measures1 + self._cputime * self._cputime) / task.measures
        s2 = self._cputime_mean_square - self._cputime_mean * self._cputime_mean
        x = self._cputime_m - self._cputime_mean
        x = x * x
        if x < s2:
            return
        self._cputime_m = self._cputime_mean
        logger.warning('cputime: %s[%s] %s %0.1f' % (self.__class__.__name__, self._taskid, self._cputime, self._cputime_m))
    def _invoke(self):
        pass
    def set_alarm(self, task, after):
        self._alarm = time.ticks_add(task._alarm, after)
        self._main.append(self)

class mainloop(object):
    def __init__(self):
        self.tasks = list()
        self.start = self.ticks()
        self._init()
    def _init(self):
        pass
    def append(self, task):
        self.tasks.append(task)
    def ticks(self):
        return time.ticks_us()
    def run(self):
        while True:
            self.dispatch()
    def dispatch(self):
        queue = self.tasks
        runnable = list()
        maxtrigger = 0
        self.tasks = list()
        self.start = self.ticks()
        for task in queue:
            task._trigger = time.ticks_diff(self.start, task._alarm)
            if task._trigger < 0:
                self.append(task)
            else:
                if maxtrigger < task._trigger:
                    maxtrigger = task._trigger
                runnable.append(task)
        while len(runnable) > 0:
            trigger = maxtrigger
            queue = runnable
            runnable = list()
            maxtrigger = 0
            for task in queue:
                if task._trigger >= trigger:
                    task.invoke()
                    continue
                if maxtrigger < task._trigger:
                    maxtrigger = task._trigger
                runnable.append(task)

class led_on(task):
    def _invoke(self):
        self._main.led.value(1)
        self._main.off.set_alarm(self, 50000)
        self.set_alarm(self, 1000000)

class led_off(task):
    def _invoke(self):
        self._main.led.value(0)

class main(mainloop):
    def _init(self):
        self.led = machine.Pin("LED", machine.Pin.OUT)
        self.on = led_on(self)
        self.off = led_off(self)
        self.led.value(1)
        self.off.set_alarm(self.on, 3000000)
        self.on.set_alarm(self.on, 4000000)

try:
    main().run()
except Exception as e:
    logger.critical('%s: %s' % (e.__class__.__name__, e.value))
