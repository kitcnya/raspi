# -*- coding: utf-8-unix -*-
# Copyright (C) 2025 kitcnya@outlook.com
# https://opensource.org/license/mit/
# SPDX-License-Identifier: MIT

import time

from logging import getLogger
logger = getLogger(__name__)

class task(object):

    taskid = 0

    def __init__(self, sequencer):
        self.taskid = task.taskid
        task.taskid += 1
        self.sequencer = sequencer
        self._alarm = sequencer._start
        self._start = sequencer._start
        self._end = sequencer._start
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
        self._start = self.sequencer.ticks()
        self.delaytime = time.ticks_diff(self._start, self._alarm)
        self.task()
        self._end = self.sequencer.ticks()
        self.cputime = time.ticks_diff(self._end, self._start)
        if self.delaytime > self.warn_delaytime:
            logger.warning('delay %s: %s' % (str(self), self.delaytime))
        if self.cputime > self.warn_cputime:
            logger.warning('cputime %s: %s' % (str(self), self.cputime))

    def task(self):
        pass

    def set_alarm(self, task, after):
        self._alarm = time.ticks_add(task._alarm, after)
        self.sequencer.append(self)

    def set_time(self, ticks = None, adjust = 0):
        if ticks is None:
            ticks = self.sequencer.ticks()
        self._alarm = time.ticks_add(ticks, adjust)

class sequencer(object):

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
