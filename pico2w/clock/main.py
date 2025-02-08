# -*- coding: utf-8-unix -*-
import os
import sys
import math
import time
import machine

from logging import basicConfig, WARNING, INFO, DEBUG
logfile = 'main.log'
logformat = '%(asctime)s %(levelname)s: %(message)s'
#basicConfig(filename = logfile, filemode = 'a', format = logformat, level = DEBUG)
basicConfig(filename = logfile, filemode = 'a', format = logformat, level = INFO)
#basicConfig(filename = logfile, filemode = 'a', format = logformat, level = WARNING)

from logging import getLogger
logger = getLogger(__name__)

logger.warning('starting up')

class task(object):

    taskid = 0

    def __init__(self, main):
        self.taskid = task.taskid
        task.taskid += 1
        self.main = main
        self._alarm = main._start
        self._start = main._start
        self._end = main._start
        self.delaytime = 0
        self.cputime = 0
        self.warn_delaytime = 1000
        self.warn_cputime = 10000
        self.init()

    def __str__(self):
        return '%s:%s' % (self.taskid, self.__class__.__name__)

    def init(self):
        pass

    def invoke(self):
        self._start = self.main.ticks()
        self.delaytime = time.ticks_diff(self._start, self._alarm)
        self.task()
        self._end = self.main.ticks()
        self.cputime = time.ticks_diff(self._end, self._start)
        if self.delaytime > self.warn_delaytime:
            logger.warning('delay %s: %s' % (str(self), self.delaytime))
        if self.cputime > self.warn_cputime:
            logger.warning('cputime %s: %s' % (str(self), self.cputime))

    def task(self):
        pass

    def set_alarm(self, task, after):
        self._alarm = time.ticks_add(task._alarm, after)
        self.main.append(self)

class mainloop(object):

    def __init__(self):
        self.tasks = list()
        self._start = self.ticks()
        self._trigger = 1000
        self._queuelen = 0
        self._debug = False
        self.init()

    def init(self):
        pass

    def append(self, task):
        self.tasks.append(task)

    def ticks(self):
        return time.ticks_us()

    def run(self):
        n = len(self.tasks)
        while n > 0:
            if n != self._queuelen:
                self.tasks.sort(key = lambda t: t._alarm)
                if self._debug:
                    logger.warning('tasks: %s' % (', '.join(['%s-%s' % (t._alarm, str(t)) for t in self.tasks])))
            self._queuelen = n
            queue = self.tasks
            self.tasks = list()
            self._start = self.ticks()
            for task in queue:
                countdown = time.ticks_diff(task._alarm, self._start)
                if countdown > self._trigger:
                    self.append(task)
                else:
                    if self._debug:
                        logger.info('trigger: %s %s-%s' % (self._start, task._alarm, str(task)))
                    task.invoke()
                    self._queuelen = 0
            if self._queuelen > 0 and self._debug:
                logger.debug('trigger: %s (no tasks)' % self._start)
            n = len(self.tasks)
        raise RuntimeError('task queue is empty')

class led_on(task):
    def task(self):
        self.main.led.value(1)

class led_off(task):
    def task(self):
        self.main.led.value(0)

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
                self.codes.append((led_on(self.main), self.next))
                self.next += self.unit
                self.codes.append((led_off(self.main), self.next))
                self.next += self.unit
            elif t == '-':
                self.codes.append((led_on(self.main), self.next))
                self.next += self.unit_long
                self.codes.append((led_off(self.main), self.next))
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

class main(mainloop):
    def init(self):
        self.led = machine.Pin("LED", machine.Pin.OUT)
        led_on(self).task()
        off = led_off(self)
        off.set_alarm(off, 5000000)
        msg = morse(self)
        msg.set_alarm(msg, 6000000)
        #         k   i  t c    n  y    a  1
        msg.tone('-.- .. - -.-. -. -.-- .-/.----///=')
        #msg.tone('...,---,...///=')
        logger.info('msg length: %s' % msg.next)

try:
    main().run()
    logger.critical('mainloop exit.')
except Exception as e:
    logger.critical('%s: %s' % (e.__class__.__name__, e.value))
