# -*- coding: utf-8-unix -*-
# Copyright (C) 2025 kitcnya@outlook.com
# https://opensource.org/license/mit/
# SPDX-License-Identifier: MIT

import time
import socket
import struct

from logging import getLogger
logger = getLogger(__name__)

class nettime(object):

    def __init__(self, server, servers, index = 0, timeout = 0.5, timezone = 32400): # 32400 = 9 * 3600
        self.ntpserver = server
        self.ntpservers = servers
        self.index = index
        self.timeout = timeout
        self.timezone = timezone
        self.request = b'\x23' + 47 * b'\0'

    def get(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        sock.settimeout(self.timeout)
        start = time.ticks_us()
        try:
            sock.sendto(self.request, (self.ntpserver, 123))
            answer, src = sock.recvfrom(64)
        except Exception as e:
            logger.error('%s: %s; %s (timeout?)' % (e.__class__.__name__, e.value, str(self.ntpserver)))
            sock.close()
            self.index += 1
            if self.index >= len(self.ntpservers):
                self.index = 0
            self.ntpserver = self.ntpservers[self.index]
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
        epoch += self.timezone
        return epoch, ticks
