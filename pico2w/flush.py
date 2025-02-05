# -*- coding: utf-8-unix -*-

import os
import sys
import re
import argparse
import subprocess as sp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('-p', '--prune', action = 'store_true')
    args = parser.parse_args()
    directory = os.path.realpath(args.directory)
    if not os.path.exists(directory):
        raise ValueError('No directory: %s' % directory)
    os.chdir(directory)

    sp.run(['mpremote', 'rtc', '--set'])

    cmd = sp.run(['mpremote', 'fs', 'ls'], stdout = sp.PIPE)
    coding = 'utf-8'
    out = cmd.stdout.decode(coding)
    remote = list()
    for line in out.split('\n'):
        m = re.fullmatch('\s*(\d+)\s+(\S+)\s*', line)
        if m is None:
            continue
        size = m.group(1)
        name = m.group(2)
        remote.append(name)

    local = list()
    for name in os.listdir('.'):
        if re.fullmatch('.*\.log', name):
            continue
        local.append(name)

    for name in remote:
        if re.fullmatch('.*\.log', name):
            sp.run(['mpremote', 'fs', 'cp', ':' + name, name])

    for name in local:
        sp.run(['mpremote', 'fs', 'cp', name, ':' + name])

    if args.prune:
        for name in remote:
            if name in local:
                continue
            print('>>> discarding %s on remote' % name)
            sp.run(['mpremote', 'fs', 'rm', name])

    sp.run(['mpremote', 'reset'])

if __name__ == '__main__':
    main()
