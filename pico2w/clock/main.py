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
        self.taskid = task.taskid
        task.taskid += 1
        self.main = main
        self._trigger = main._start
        self._alarm = main._start
        self._start = main._start
        self._end = main._start
        self.delaytime = 0
        self.delaytime_mean = 0
        self.delaytime_mean_square = 0
        self.delaytime_level = 0
        self.cputime = 0
        self.cputime_mean = 0
        self.cputime_mean_square = 0
        self.cputime_level = 0

    def invoke(self):
        self._start = self.main.ticks()
        self.delaytime = time.ticks_diff(self._start, self._alarm)
        self.task()
        self._end = self.main.ticks()
        self.cputime = time.ticks_diff(self._end, self._start)

        self.delaytime_mean = (self.delaytime_mean * task.measures1 + self.delaytime) // task.measures
        self.delaytime_mean_square = (self.delaytime_mean_square * task.measures1 + self.delaytime * self.delaytime) // task.measures
        s2 = self.delaytime_mean_square - self.delaytime_mean * self.delaytime_mean
        x = self.delaytime_level - self.delaytime_mean
        x = x * x
        if x > s2:
            self.delaytime_level = self.delaytime_mean
            logger.warning('delaytime: %s[%s] %s %s' % (self.__class__.__name__, self.taskid, self.delaytime, self.delaytime_level))

        self.cputime_mean = (self.cputime_mean * task.measures1 + self.cputime) // task.measures
        self.cputime_mean_square = (self.cputime_mean_square * task.measures1 + self.cputime * self.cputime) // task.measures
        s2 = self.cputime_mean_square - self.cputime_mean * self.cputime_mean
        x = self.cputime_level - self.cputime_mean
        x = x * x
        if x > s2:
            self.cputime_level = self.cputime_mean
            logger.warning('cputime: %s[%s] %s %s' % (self.__class__.__name__, self.taskid, self.cputime, self.cputime_level))

    def task(self):
        pass

    def set_alarm(self, task, after):
        self._alarm = time.ticks_add(task._alarm, after)
        self.main.append(self)

class mainloop(object):

    def __init__(self):
        self.tasks = list()
        self._start = self.ticks()
        self.init()

    def init(self):
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
        self._start = self.ticks()
        for task in queue:
            task._trigger = time.ticks_diff(self._start, task._alarm)
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
    def task(self):
        self.main.led.value(1)
        self.main.off.set_alarm(self, 50000)
        self.set_alarm(self, 1000000)

class led_off(task):
    def task(self):
        self.main.led.value(0)

class main(mainloop):
    def init(self):
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
