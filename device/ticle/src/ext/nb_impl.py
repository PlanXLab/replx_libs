__version__ = "1.0.0"
__author__ = "PlanX Lab Development Team"

from . import (
    utime,
    micropython
)


# Qty domains(Upper 8 bits = domain, lower 8 bits = detail)
def Q(dom, id): 
    return (dom<<8)|id

DOM_MOTION   = 1
DOM_ORIENT   = 2
DOM_DIST     = 3
DOM_ENV      = 4
DOM_LIGHT    = 5
DOM_EVENT    = 6
DOM_INPUT    = 7

Q_ACC        = Q(DOM_MOTION, 1)   # m/s^2,                   (3,)
Q_GYRO       = Q(DOM_MOTION, 2)   # rad/s,                   (3,)
Q_MAG        = Q(DOM_MOTION, 3)   # µT,                      (3,)
Q_LINACC     = Q(DOM_MOTION, 4)   # m/s^2,                   (3,)
Q_GRAV       = Q(DOM_MOTION, 5)   # m/s^2,                   (3,)
Q_EULER      = Q(DOM_ORIENT, 1)   # rad,                     (3,)
Q_QUAT       = Q(DOM_ORIENT, 2)   # unitless,                (4,)
Q_ANGLE      = Q(DOM_ORIENT, 3)   # rad,                     ()
Q_ANGVEL     = Q(DOM_ORIENT, 4)   # rad/s,                   ()
Q_TURN       = Q(DOM_ORIENT, 5)   # unitless turns,          ()
Q_DIST       = Q(DOM_DIST,   1)   # m,                       (), (H,W) possible
Q_ILLUM      = Q(DOM_LIGHT,  1)   # lux,                     ()
Q_TEMP       = Q(DOM_ENV,    1)   # °C,                      ()
Q_HUM        = Q(DOM_ENV,    2)   # %RH,                     ()
Q_PRESS      = Q(DOM_ENV,    3)   # Pa,                      ()
Q_GAS        = Q(DOM_ENV,    4)   # Ohm,                     ()
Q_IAQ        = Q(DOM_ENV,    5)   # IAQ index,               ()
Q_GESTURE    = Q(DOM_EVENT,  1)   # enum/int,                ()
Q_IR_CODE    = Q(DOM_EVENT,  2)   # int/bytes,               ()
Q_COLOR      = Q(DOM_EVENT,  3)   # RGB packed int 0xRRGGBB, ()
Q_BTN_STATE  = Q(DOM_INPUT,  1)   # 0/1,                     ()
Q_BTN_EVENT  = Q(DOM_INPUT,  2)   # int(CLICK/DBL/LONG),     ()

U_NONE       = 0
U_MS2        = 1
U_RAD_S      = 2
U_UT         = 3
U_RAD        = 4
U_M          = 5
U_LUX        = 6
U_DEGC       = 7
U_RH         = 8
U_PA         = 9
U_OHM        = 10

F_SENSOR     = 1
F_ENU        = 2
F_NED        = 3

OK           = micropython.const(0)
CALIBRATING  = micropython.const(1 << 0)
OVERTIME     = micropython.const(1 << 1)
BUS_ERR      = micropython.const(1 << 2)
SATURATED    = micropython.const(1 << 3)
STALE        = micropython.const(1 << 4)


class ChannelInfo:
    __slots__=("qty","unit","frame","shape","nominal_rate_hz","range","resolution")

    def __init__(self, qty, unit, frame, shape, nominal_rate_hz=0.0, range=None, resolution=None):
        self.qty=qty
        self.unit=unit
        self.frame=frame
        self.shape=shape
        self.nominal_rate_hz=float(nominal_rate_hz)
        self.range=range
        self.resolution=resolution


class Sample:
    __slots__=("qty","unit","frame","shape","value","status","ts_us","src")

    def __init__(self, qty, unit, frame, shape, value, status=0, src=""):
        self.qty=qty
        self.unit=unit
        self.frame=frame
        self.shape=shape
        self.value=value
        self.status=status
        self.ts_us=utime.ticks_us()
        self.src=src


class NBAdapterBase:
    __slots__ = ("_subs", "_last", "_stats")

    def __init__(self):
        self._subs = {}
        self._last = {}
        self._stats = {"reads":0, "fails":0, "skips":0, "avg_us":0.0, "max_us":0, "last_err":OK}

        for ch in self.channels():
            self._subs[ch.qty] = []
            self._last[ch.qty] = None

    def channels(self):
        raise NotImplementedError

    def _update_impl(self, *args, **kwargs):
        raise NotImplementedError

    def start(self):
        pass

    def stop(self):
        pass

    def subscribe(self, qty, cb):
        lst = self._subs.get(qty)
        if lst is not None and (cb not in lst):
            lst.append(cb)

    def unsubscribe(self, qty, cb):
        lst = self._subs.get(qty)
        if lst is not None:
            try: 
                lst.remove(cb)
            except ValueError: 
                pass

    def last(self, qty):
        return self._last.get(qty)

    def _emit(self, sample: Sample):
        self._last[sample.qty] = sample
        for cb in self._subs.get(sample.qty, ()):
            try: cb(sample)
            except Exception:
                pass

    def update_once(self, *args, **kwargs):
        t0 = utime.ticks_us()
        try:
            ok = bool(self._update_impl(*args, **kwargs))
            dt_us = utime.ticks_diff(utime.ticks_us(), t0)
            self._stats["reads"] += 1
            a = 0.1
            self._stats["avg_us"] = (1-a)*self._stats["avg_us"] + a*dt_us
            if dt_us > self._stats["max_us"]: 
                self._stats["max_us"] = dt_us
            self._stats["last_err"] = OK
            return ok
        except Exception:
            self._stats["fails"] += 1
            self._stats["last_err"] = BUS_ERR
            return False

    @property
    def stats(self):
        return self._stats