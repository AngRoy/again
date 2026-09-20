"""Keep a demo host awake while this process is running; no permanent power changes."""
import ctypes
import os
import signal
import time

running=True

def stop(*_):
    global running
    running=False

for signum in (signal.SIGINT,signal.SIGTERM):
    signal.signal(signum,stop)

if os.name!='nt':
    raise SystemExit('This optional helper is only needed on Windows.')
api=ctypes.windll.kernel32.SetThreadExecutionState
api.argtypes=[ctypes.c_uint];api.restype=ctypes.c_uint
try:
    if not api(0x80000000|0x00000001):
        raise OSError('Windows did not accept the temporary keep-awake request')
    while running:
        time.sleep(10)
finally:
    api(0x80000000)
