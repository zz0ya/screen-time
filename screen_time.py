#!/usr/bin/env python

import datetime
import json
import os
import re
import time
import signal
import subprocess
import sys
from pathlib import Path

if not 'DISPLAY' in os.environ:
    sys.exit('This proram is meant to be executed inside X Window session')

LOG = Path.home() / 'screentime.jsonl'

CHECK_INTERVAL = 10
TIME_FORMAT = '%F %T'

def dt(t):
    return t.strftime(TIME_FORMAT)

def ts(s):
    return str(datetime.timedelta(seconds=s))

def now_dt():
    return dt(now())

def finish(_sig, _frame):
    save_log()
    sys.exit(0)

def now():
    return datetime.datetime.now()

def save_log():
    with open(LOG, 'a', encoding='ascii') as log:
        line = json.dumps(collected_data())
        log.write(f"{line}\n")

def collected_data():
    return {'boot_at': dt(boot_at()),
            'started_at': STARTED_AT,
            'ended_at': now_dt(),
            'total_on': ts(on_time),
            'total_off': ts(off_time),
            'switches': list(map(dt, switches))}

def print_state(_sig, _frame):
    print(f"on: {ts(on_time)}, off: {ts(off_time)}, switches: {len(switches)}")

MIN_LOG_PERIOD = 90
def is_period_short(t):
    return len(switches) > 0 and (t - switches[-1]).seconds < MIN_LOG_PERIOD

def register_switch():
    t = now()
    if is_period_short(t):
        switches.pop()
        return
    switches.append(t)

signal.signal(signal.SIGINT, finish)
signal.signal(signal.SIGHUP, finish)
signal.signal(signal.SIGTERM, finish)
signal.signal(signal.SIGINFO, print_state)

STATE_COMMAND = "xset q | grep -q 'Monitor is On'"
def is_monitor_on():
    return 0 == os.system(STATE_COMMAND)

BOOTTIME_COMMAND = 'sysctl -n kern.boottime'
def boot_at():
    res = subprocess.check_output(BOOTTIME_COMMAND, text=True, shell=True)
    secs = re.search(r'\d+', res).group(0)
    return datetime.datetime.fromtimestamp(int(secs))

on_time = 0
off_time = 0
switches = []
STARTED_AT = now_dt()
prev_state = None

while True:
    is_on = is_monitor_on()
    if is_on:
        on_time += CHECK_INTERVAL
    else:
        off_time += CHECK_INTERVAL
    if is_on != prev_state:
        prev_state = is_on
        register_switch()
    time.sleep(CHECK_INTERVAL)

