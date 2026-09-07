#!/usr/bin/env python

import datetime
import os
import re
import time
import signal
import subprocess
import sys
from pathlib import Path

LOG = Path.home() / 'screentime.log'

CHECK_INTERVAL = 10
TIME_FORMAT = '%F %R'

def dt(t):
    return t.strftime(TIME_FORMAT)

def ts(s):
    return str(datetime.timedelta(seconds=s))

on_time = 0
off_time = 0

def finish(_sig, _frame):
    save_log()
    sys.exit(0)

def now():
    return datetime.datetime.now()

def save_log():
    with open(LOG, 'a', encoding='ascii') as log:
        log.write(f"Started at: {started_at}\n")
        log.write(f"On: {ts(on_time)}\n")
        if off_time > 0:
            log.write(f"Off: {ts(off_time)}\n")
        if switches_count > 0:
            log.write(f"Switches: {switches_count}\n")
        log.write(f"Finished at: {fin_at}\n")

def print_state(_sig, _frame):
    print(f"on: {ts(on_time)}, off: {ts(off_time)}, switches: {switches_count}")

signal.signal(signal.SIGINT, finish)
signal.signal(signal.SIGHUP, finish)
signal.signal(signal.SIGTERM, finish)
signal.signal(signal.SIGINFO, print_state)

STATE_COMMAND = "xset q | grep 'Monitor is On' > /dev/null"
def is_monitor_on():
    return 0 == os.system(STATE_COMMAND)


started_at = now()
prev_state = False
switches_count = 0

while True:
    is_on = is_monitor_on()
    if is_on:
        on_time += CHECK_INTERVAL
    else:
        off_time += CHECK_INTERVAL
    if is_on != prev_state:
        prev_state = is_on
        switches_count += 1
    time.sleep(CHECK_INTERVAL)

