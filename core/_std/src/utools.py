# @package: utools
# @version: 1.1.0
# @type: core
# @category: utility
# @interface: none
# @depends: none
# @platforms: *
# @tags: utility, clamp, map, range, random
# @author: PlanXLab Development Team

import os
import time
import micropython

@micropython.native
def clamp(val: float, lo: float, hi: float) -> float:
    if lo > hi:
        raise ValueError("Lower bound must be <= upper bound")
    return lo if val < lo else hi if val > hi else val

@micropython.native
def map(x: float, min_i: float, max_i: float, min_o: float, max_o: float) -> float:
    if max_i == min_i:
        raise ZeroDivisionError("Input range cannot be zero")
    return (x - min_i) * (max_o - min_o) / (max_i - min_i) + min_o

@micropython.native
def xrange(start: float, stop: float | None = None, step: float | None = None) -> iter[float]:
    if stop is None:
        stop, start = start, 0.0

    if step is None:
        step = 1.0 if stop >= start else -1.0

    if step == 0.0:
        raise ValueError("step must not be zero")

    if (stop - start) * step <= 0.0:
        return

    s_step = "{:.16f}".format(abs(step)).rstrip('0').rstrip('.')
    decimals = len(s_step.split('.')[1]) if '.' in s_step else 0

    idx = 0
    while True:
        value = start + idx * step
        if (step > 0 and value >= stop) or (step < 0 and value <= stop):
            break
        yield round(value, decimals)
        idx += 1

def rand(size: int = 4) -> int:
    if size <= 0 or size > 8:
        raise ValueError("Size must be between 1 and 8 bytes")
    
    return int.from_bytes(os.urandom(size), "big")

@micropython.native
def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    i = int(h // 60) % 6
    f = (h / 60) - i
    p = int(v * (1 - s) * 255)
    q = int(v * (1 - f * s) * 255)
    t = int(v * (1 - (1 - f) * s) * 255)
    v = int(v * 255)
    if   i == 0: return v, t, p
    elif i == 1: return q, v, p
    elif i == 2: return p, v, t
    elif i == 3: return p, q, v
    elif i == 4: return t, p, v
    else:        return v, p, q

@micropython.native
def rgb_to_hsv(r: int, g: int, b: int) -> tuple[int, float, float]:
    r, g, b = r / 255, g / 255, b / 255
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val
    
    v = max_val
    s = 0 if max_val == 0 else diff / max_val
    
    if diff == 0:
        h = 0
    elif max_val == r:
        h = 60 * (((g - b) / diff) % 6)
    elif max_val == g:
        h = 60 * (((b - r) / diff) + 2)
    else:
        h = 60 * (((r - g) / diff) + 4)
    
    return (int(h) % 360, s, v)

def intervalChecker(interval_ms: int) -> callable:
    if not isinstance(interval_ms, int) or interval_ms <= 0:
        raise ValueError("Interval must be a positive integer")

    interval_us = interval_ms * 1000
    current_tick = time.ticks_us()

    def check_interval() -> bool:
        nonlocal current_tick

        now_us = time.ticks_us()
        elapsed_us = time.ticks_diff(now_us, current_tick)
        if elapsed_us >= interval_us:
            steps = elapsed_us // interval_us
            current_tick = time.ticks_add(current_tick, steps * interval_us)
            return True
        return False

    return check_interval
