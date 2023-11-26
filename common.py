import os
import time
platform = "circuitpython"
supervisor = None
try:
    import supervisor
except:
    platform = "micropython"
    print("micropython, no supervisor module exists, use time.ticks_ms instead")
hashlib = None
try:
    import adafruit_hashlib as hashlib
except:
    import hashlib

BUF_SIZE = 65536
_TICKS_PERIOD = const(1<<29)
_TICKS_MAX = const(_TICKS_PERIOD-1)
_TICKS_HALFPERIOD = const(_TICKS_PERIOD//2)


def ticks_ms():
    if supervisor:
        return supervisor.ticks_ms()
    else:
        return time.ticks_ms()


def sleep_ms(t):
    time.sleep(t / 1000.0)


def ticks_add(ticks, delta):
    # "Add a delta to a base number of ticks, performing wraparound at 2**29ms."
    return (ticks + delta) % _TICKS_PERIOD


def ticks_diff(ticks1, ticks2):
    # "Compute the signed difference between two ticks values, assuming that they are within 2**28 ticks"
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff


def ticks_less(ticks1, ticks2):
    # "Return true iff ticks1 is less than ticks2, assuming that they are within 2**28 ticks"
    return ticks_diff(ticks1, ticks2) < 0


def sha1sum(content):
    #'''param content must be unicode, result is string'''
    if platform == "circuitpython":
        m = hashlib.sha1(content.encode("utf-8"))
        m.digest()
        result = m.hexdigest()
    else:
        m = hashlib.sha1(content.encode("utf-8"))
        result = m.digest().hex()
    return result


def md5twice(content):
    #'''param content must be unicode, result is string'''
    if platform == "circuitpython":
        m = hashlib.md5(content.encode("utf-8")).hexdigest()
        result = hashlib.md5(m).hexdigest()
    else:
        result = None
    return result


def exists(path):
    r = False
    try:
        if os.stat(path):
            r = True
    except OSError:
        pass
    return r


def path_join(*args):
    path = args[0]
    for p in args[1:]:
        if path.endswith("/"):
            path = path[:-1]
        p = p.strip("/")
        if p.startswith(".."):
            path = "/".join(path.split("/")[:-1])
            path += "/" + p[2:]
        else:
            path += "/" + p
    if args[-1].endswith("/"):
        if not path.endswith("/"):
            path += "/"
    if not path.startswith("/"):
        path = "/" + path
    return path
