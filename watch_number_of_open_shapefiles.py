#!/usr/bin/env python

import os
import sys
import time
from subprocess import Popen, PIPE

def call(cmd, silent=False):
    p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return stdout.strip()

if not len(sys.argv) > 1:
    sys.exit('usage: %s <file> or <process id>' % sys.argv[0])

process_id = None

if os.path.exists(sys.argv[1]):
    cmd = 'fuser %s' % sys.argv[1]
    process_id = call(cmd)
else:
    process_id = sys.argv[1]

cmd = 'lsof -p %s -F n' % process_id

while True:
    try:
        time.sleep(.5)
        open_files = call(cmd).split('\n')
        shps = [i.strip() for i in open_files if i.endswith('.shp')]
        print len(shps)
    except KeyboardInterrupt:
        sys.exit()