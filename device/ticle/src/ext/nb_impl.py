__version__ = "1.0.0"
__author__ = "PlanX Lab Development Team"

from . import (
    utime,
    micropython
)


# Qty domains(Upper 8 bits = domain, lower 8 bits = detail)
def Q(dom, id): 
    return (dom<<8)|id

# Core sensor domains (1-7)
DOM_MOTION   = 1   # Accelerometer, Gyroscope, Magnetometer
DOM_ORIENT   = 2   # Euler angles, Quaternion, Angle, Angular velocity
DOM_DIST     = 3   # Distance, Proximity, ToF, Ultrasonic
DOM_ENV      = 4   # Temperature, Humidity, Pressure, Gas, Air Quality
DOM_LIGHT    = 5   # Illuminance, Color, UV
DOM_EVENT    = 6   # Gesture, IR code, Color detection
DOM_INPUT    = 7   # Button state, Button event, Touch

# Extended sensor domains (8-15)
DOM_BIO      = 8   # Biometric: EMG, Pulse, Fingerprint, SpO2
DOM_AUDIO    = 9   # Audio: Microphone, Sound level, Frequency
DOM_FLOW     = 10  # Flow: Water flow, Liquid level, Soil moisture
DOM_FORCE    = 11  # Force: Load cell, FSR, Vibration, Weight
DOM_POSITION = 12  # Position: GPS, Location, Compass
DOM_CAMERA   = 13  # Camera: Image, Video, Thermal
DOM_SPECIAL  = 14  # Special: Geiger, Barcode, Magstripe, Coin
# DOM_RESERVED = 15  # Reserved for future use

# Core sensor quantity types (DOM_MOTION, DOM_ORIENT, DOM_DIST, DOM_ENV, DOM_LIGHT, DOM_EVENT, DOM_INPUT)
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

# Extended sensor quantity types (DOM_BIO, DOM_AUDIO, DOM_FLOW, DOM_FORCE, DOM_POSITION, DOM_CAMERA, DOM_SPECIAL)
Q_EMG        = Q(DOM_BIO,     1)  # mV,                      ()
Q_PULSE      = Q(DOM_BIO,     2)  # BPM,                     ()
Q_FINGERPRINT= Q(DOM_BIO,     3)  # ID/confidence,           ()
Q_SPO2       = Q(DOM_BIO,     4)  # %,                       ()
Q_ECG        = Q(DOM_BIO,     5)  # mV,                      ()
Q_SOUND_LEVEL= Q(DOM_AUDIO,   1)  # dB,                      ()
Q_FREQUENCY  = Q(DOM_AUDIO,   2)  # Hz,                      ()
Q_AUDIO_RAW  = Q(DOM_AUDIO,   3)  # sample value,            (N,)
Q_WATER_FLOW = Q(DOM_FLOW,    1)  # L/min,                   ()
Q_LIQUID_LVL = Q(DOM_FLOW,    2)  # m or %,                  ()
Q_SOIL_MOIST = Q(DOM_FLOW,    3)  # %,                       ()
Q_FORCE      = Q(DOM_FORCE,   1)  # N,                       ()
Q_WEIGHT     = Q(DOM_FORCE,   2)  # kg,                      ()
Q_VIBRATION  = Q(DOM_FORCE,   3)  # bool/level,              ()
Q_LATITUDE   = Q(DOM_POSITION,1)  # degrees,                 ()
Q_LONGITUDE  = Q(DOM_POSITION,2)  # degrees,                 ()
Q_ALTITUDE   = Q(DOM_POSITION,3)  # m,                       ()
Q_GPS_FIX    = Q(DOM_POSITION,4)  # bool,                    ()
Q_IMAGE      = Q(DOM_CAMERA,  1)  # pixel values,            (H,W,C)
Q_THERMAL    = Q(DOM_CAMERA,  2)  # °C,                      (H,W)
Q_RADIATION  = Q(DOM_SPECIAL, 1)  # CPM or µSv/h,            ()
Q_BARCODE    = Q(DOM_SPECIAL, 2)  # str/bytes,               ()
Q_COIN       = Q(DOM_SPECIAL, 3)  # bool/value,              ()

# Unit constants
U_NONE       = 0   # Unitless
U_MS2        = 1   # m/s^2 (acceleration)
U_RAD_S      = 2   # rad/s (angular velocity)
U_UT         = 3   # µT (magnetic field)
U_RAD        = 4   # rad (angle)
U_M          = 5   # m (distance)
U_LUX        = 6   # lux (illuminance)
U_DEGC       = 7   # °C (temperature)
U_RH         = 8   # %RH (relative humidity)
U_PA         = 9   # Pa (pressure)
U_OHM        = 10  # Ohm (resistance)
U_MV         = 11  # mV (millivolt)
U_BPM        = 12  # BPM (beats per minute)
U_DB         = 13  # dB (decibel)
U_HZ         = 14  # Hz (frequency)
U_L_MIN      = 15  # L/min (liters per minute)
U_N          = 16  # N (newton, force)
U_KG         = 17  # kg (kilogram, mass)
U_DEG        = 18  # degrees (latitude/longitude)
U_CPM        = 19  # CPM (counts per minute)
U_USV_H      = 20  # µSv/h (microsievert per hour)

F_SENSOR     = 1
F_ENU        = 2
F_NED        = 3

OK           = micropython.const(0)
CALIBRATING  = micropython.const(1 << 0)  # Sensor is calibrating or signal is weak
OVERTIME     = micropython.const(1 << 1)  # Update took too long
BUS_ERR      = micropython.const(1 << 2)  # I2C/SPI communication error
SATURATED    = micropython.const(1 << 3)  # Sensor signal saturated (too strong)
STALE        = micropython.const(1 << 4)  # Data is stale or outdated
NO_SIGNAL    = micropython.const(1 << 5)  # No sensor signal detected (e.g., no magnet, no GPS fix)


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