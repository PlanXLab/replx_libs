# @package: utools
# @version: 1.1.0
# @type: core
# @category: utility
# @interface: none
# @depends: none
# @platforms: EFR32MG
# @tags: utility, clamp, map, range, random
# @author: PlanXLab Development Team

import uos
import utime

def clamp(val: float, lo: float, hi: float) -> float:
    if lo > hi:
        raise ValueError("Lower bound must be <= upper bound")
    return lo if val < lo else hi if val > hi else val

def map(x: float, min_i: float, max_i: float, min_o: float, max_o: float) -> float:
    if max_i == min_i:
        raise ZeroDivisionError("Input range cannot be zero")
    return (x - min_i) * (max_o - min_o) / (max_i - min_i) + min_o

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
    
    return int.from_bytes(uos.urandom(size), "big")

def intervalChecker(interval_ms: int) -> callable:
    if not isinstance(interval_ms, int) or interval_ms <= 0:
        raise ValueError("Interval must be a positive integer")

    interval_us = interval_ms * 1000
    current_tick = utime.ticks_us()

    def check_interval() -> bool:
        nonlocal current_tick

        now_us = utime.ticks_us()
        elapsed_us = utime.ticks_diff(now_us, current_tick)
        if elapsed_us >= interval_us:
            steps = elapsed_us // interval_us
            current_tick = utime.ticks_add(current_tick, steps * interval_us)
            return True
        return False

    return check_interval
