# @package: us
# @version: 3.4
# @type: device-specific
# @category: distance
# @sensor_type: B
# @interface: GPIO
# @depends: ufilter
# @platforms: rp2
# @tags: ultrasonic, distance, sr04, hc-sr04, pio, multi-sensor, kalman
# @author: PlanXLab Development Team

import time
import array
import machine
import micropython
import rp2
from rp2 import PIO, StateMachine
from ufilter import Kalman1D

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, autopush=False, push_thresh=32)
def _sr04_pio_prog():
    pull(block)          
    
    set(pins, 1)            [9]
    set(pins, 0)
    
    mov(x, osr)           
    label("wait_echo")
    jmp(pin, "measure")
    jmp(x_dec, "wait_echo")
    jmp("timeout")
    
    label("measure")
    mov(x, invert(null))
    label("count")
    jmp(pin, "continue")
    jmp("done")
    label("continue")
    jmp(x_dec, "count")
    
    label("done")
    mov(isr, invert(x))
    push()
    irq(rel(0))
    
    label("timeout")
    set(x, 0)
    mov(isr, x)
    push()
    irq(rel(0))

def find_free_sm_pio2(count: int) -> list[int]:
    @rp2.asm_pio()
    def _nop():
        nop()
    
    available = []

    for i in (8, 9, 10, 11):
        try:
            sm = rp2.StateMachine(i, _nop)
            sm.active(0)
            available.append(i)
            if len(available) >= count:
                return available
        except:
            pass

    if len(available) < count:
        raise RuntimeError(f"Need {count} SM on PIO2, only {len(available)} available")
    return available


class SR04:
    _PIO_FREQ = 1_000_000
    _TIMEOUT_US = 38000
    _MIN_M = 0.02
    _MAX_M = 4.0
    _MIN_INTERVAL_US = 60000

    def __init__(self, sensor_configs: list[tuple[int, int]] | None = None, *,
                 trig: int | list[int] | None = None,
                 echo: int | list[int] | None = None,
                 temp_c: float = 20.0, R: int = 25, Q: int = 4):
        if sensor_configs is None:
            if trig is None or echo is None:
                raise ValueError("Provide sensor_configs or both trig and echo")
            if isinstance(trig, int):
                trig = [trig]
            if isinstance(echo, int):
                echo = [echo]
            sensor_configs = [(t, e) for t, e in zip(trig, echo)]
        if not sensor_configs:
            raise ValueError("At least one sensor configuration must be provided")
        
        if not (-40.0 <= temp_c <= 85.0):
            raise ValueError("Temperature must be between -40°C and +85°C")
        
        n = len(sensor_configs)
        
        sm_list = find_free_sm_pio2(n)
        
        max_sm = 12
        for s in sm_list:
            if not (0 <= s < max_sm):
                raise ValueError(f"SM {s} out of range (0-{max_sm-1})")
        
        self._n = n
        self._sm_ids = sm_list
        self._trig_pins = [cfg[0] for cfg in sensor_configs]
        self._echo_pins = [cfg[1] for cfg in sensor_configs]
        self._echo_pin_objs = []
        
        self._sms: list[StateMachine] = []
        self._sm_to_idx = {}
        
        try:
            for i, (trig, echo) in enumerate(sensor_configs):
                sm_id = sm_list[i]
                trig_pin = machine.Pin(trig, machine.Pin.OUT, value=0)
                echo_pin = machine.Pin(echo, machine.Pin.IN)
                self._echo_pin_objs.append(echo_pin)
                
                sm_obj = StateMachine(
                    sm_id,
                    _sr04_pio_prog,
                    freq=self._PIO_FREQ,
                    set_base=trig_pin,
                    in_base=echo_pin,
                    jmp_pin=echo_pin,
                )
                self._sms.append(sm_obj)
                self._sm_to_idx[id(sm_obj)] = i
        except Exception as e:
            for sm_obj in self._sms:
                try:
                    sm_obj.active(0)
                except Exception:
                    pass
            raise OSError(f"Failed to initialize PIO: {e}")
        
        self._filters = [Kalman1D(R=float(R)/10000.0, Q=float(Q)/10000.0) for _ in range(n)]
        
        self._temp_c = array.array('f', [float(temp_c)] * n)
        self._last_m = array.array('f', [-1.0] * n)
        self._last_time = array.array('L', [0] * n)
        
        self._user_callbacks = [None] * n
        self._measurement_enabled = [False] * n
        self._pending_results = [None] * n
        self._callback_pending = [False] * n
        self._callback_dispatchers = [self._make_callback_dispatcher(i) for i in range(n)]
        self._timers = [machine.Timer(-1) for _ in range(n)]
        self._timer_running = [False] * n   # True only after timer.init() is called
        self._timer_callbacks = [self._make_timer_callback(i) for i in range(n)]
        
        self._view = SR04._View(self)
        
        for i, sm_obj in enumerate(self._sms):
            sm_obj.irq(self._make_irq_handler(i))

    def _make_callback_dispatcher(self, idx: int):
        def dispatcher(_):
            self._callback_pending[idx] = False
            cb = self._user_callbacks[idx]
            if cb is not None:
                try:
                    cb((self._trig_pins[idx], self._pending_results[idx]))
                except Exception:
                    pass
        return dispatcher

    def _make_timer_callback(self, idx: int):
        def timer_callback(_t):
            if self._measurement_enabled[idx]:
                self._trigger_single(idx)
        return timer_callback

    def _make_irq_handler(self, idx: int):
        def handler(sm):
            if not self._measurement_enabled[idx]:
                return
            
            result = None
            if sm.rx_fifo() > 0:
                count = sm.get()
                
                if 0 < count < self._TIMEOUT_US:
                    now = time.ticks_us()
                    last = self._last_time[idx]
                    if last > 0:
                        dt = time.ticks_diff(now, last) / 1_000_000.0
                    else:
                        dt = 0.06
                    self._last_time[idx] = now
                    
                    speed_factor = self._m_per_count(self._temp_c[idx])
                    raw_m = count * speed_factor
                    
                    if self._MIN_M <= raw_m <= self._MAX_M:
                        filtered_m = self._filters[idx].update(raw_m, dt)
                        result = max(self._MIN_M, min(filtered_m, self._MAX_M))
                        self._last_m[idx] = result
            
            self._pending_results[idx] = result
            
            cb = self._user_callbacks[idx]
            if cb is not None and not self._callback_pending[idx]:
                self._callback_pending[idx] = True
                try:
                    micropython.schedule(self._callback_dispatchers[idx], 0)
                except RuntimeError:
                    self._callback_pending[idx] = False
                    pass
            
            if self._measurement_enabled[idx]:
                self._schedule_next(idx)
        
        return handler

    def _schedule_next(self, idx: int):
        now = time.ticks_us()
        elapsed = time.ticks_diff(now, self._last_time[idx])
        
        if elapsed >= self._MIN_INTERVAL_US:
            self._trigger_single(idx)
        else:
            delay_us = self._MIN_INTERVAL_US - elapsed
            self._timer_running[idx] = True
            self._timers[idx].init(
                mode=machine.Timer.ONE_SHOT,
                period=max(1, delay_us // 1000),
                callback=self._timer_callbacks[idx]
            )

    def _trigger_single(self, idx: int):
        if self._echo_pin_objs[idx].value() == 1:
            return
        sm_obj = self._sms[idx]
        while sm_obj.rx_fifo() > 0:
            sm_obj.get()
        sm_obj.active(0)
        sm_obj.restart()  
        sm_obj.active(1)
        sm_obj.put(self._TIMEOUT_US // 2)

    def __getitem__(self, idx: int | slice) -> "_View":
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(self._n)))
            return self._view._set(indices)
        elif isinstance(idx, int):
            if not (0 <= idx < self._n):
                raise IndexError("Sensor index out of range")
            return self._view._set([idx])
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        return self._n

    def deinit(self) -> None:
        for i in range(self._n):
            self._measurement_enabled[i] = False
        for i, timer in enumerate(self._timers):
            if self._timer_running[i]:
                try:
                    timer.deinit()
                except Exception:
                    pass
                self._timer_running[i] = False
        for sm_obj in self._sms:
            try:
                sm_obj.irq(None)
                sm_obj.active(0)
            except Exception:
                pass
        self._sms.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def read(self, timeout_us: int | None = None) -> float:
        result = self._measure_single(0, timeout_us or self._TIMEOUT_US)
        return result if result is not None else float('nan')

    @property
    def last(self) -> float:
        return self._last_m[0]

    def trigger(self) -> None:
        if self._echo_pin_objs[0].value() == 1:
            return 
        sm = self._sms[0]
        while sm.rx_fifo() > 0:
            sm.get()
        sm.active(0)
        sm.restart()
        sm.active(1)
        sm.put(self._TIMEOUT_US // 2)

    def ready(self) -> bool:
        return self._sms[0].rx_fifo() > 0

    def result(self) -> float:
        sm = self._sms[0]
        if sm.rx_fifo() == 0:
            return float('nan')
        count = sm.get()
        sm.active(0)
        if 0 < count < self._TIMEOUT_US:
            raw_m = count * self._m_per_count(self._temp_c[0])
            if self._MIN_M <= raw_m <= self._MAX_M:
                filtered_m = self._filters[0].update(raw_m, 0.06)
                r = max(self._MIN_M, min(filtered_m, self._MAX_M))
                self._last_m[0] = r
                return r
        return float('nan')

    def reset_filter(self) -> None:
        """Reset Kalman filter state for all sensors."""
        for f in self._filters:
            f.reset()

    def _wait_echo_idle(self, idx: int, timeout_ms: int = 10) -> bool:
        """Block until echo pin is LOW. Returns False on timeout."""
        pin = self._echo_pin_objs[idx]
        if pin.value() == 0:
            return True
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while pin.value() == 1:
            if time.ticks_diff(time.ticks_ms(), deadline) >= 0:
                return False
            time.sleep_us(50)
        return True

    def _m_per_count(self, temp: float) -> float:
        speed_ms = 331.3 + 0.606 * temp
        return speed_ms / 1_000_000

    def _trigger_all(self):
        for i in range(self._n):
            self._trigger_single(i)

    def _read_all(self, timeout_us: int = 38000) -> list[float | None]:
        results = [None] * self._n
        deadline = time.ticks_add(time.ticks_us(), timeout_us + 1000)
        pending = set(range(self._n))
        
        while pending and time.ticks_diff(deadline, time.ticks_us()) > 0:
            for i in list(pending):
                if self._sms[i].rx_fifo() > 0:
                    count = self._sms[i].get()
                    self._sms[i].active(0)
                    
                    if 0 < count < self._TIMEOUT_US:
                        speed_factor = self._m_per_count(self._temp_c[i])
                        raw_m = count * speed_factor
                        
                        if self._MIN_M <= raw_m <= self._MAX_M:
                            filtered_m = self._filters[i].update(raw_m, 0.06)
                            results[i] = max(self._MIN_M, min(filtered_m, self._MAX_M))
                            self._last_m[i] = results[i]
                    
                    pending.discard(i)
            
            time.sleep_us(10)
        
        for i in pending:
            self._sms[i].active(0)
        
        return results

    def _measure_single(self, idx: int, timeout_us: int = 38000) -> float | None:
        if not self._wait_echo_idle(idx, timeout_ms=10):
            return None
        sm_obj = self._sms[idx]
        while sm_obj.rx_fifo() > 0:
            sm_obj.get()
        sm_obj.active(0)
        sm_obj.restart() 
        sm_obj.active(1)
        sm_obj.put(self._TIMEOUT_US // 2) 
        
        deadline = time.ticks_add(time.ticks_us(), timeout_us + 1000)
        
        while time.ticks_diff(deadline, time.ticks_us()) > 0:
            if sm_obj.rx_fifo() > 0:
                count = sm_obj.get()
                sm_obj.active(0)
                
                if 0 < count < self._TIMEOUT_US:
                    speed_factor = self._m_per_count(self._temp_c[idx])
                    raw_m = count * speed_factor
                    
                    if self._MIN_M <= raw_m <= self._MAX_M:
                        filtered_m = self._filters[idx].update(raw_m, 0.06)
                        result = max(self._MIN_M, min(filtered_m, self._MAX_M))
                        self._last_m[idx] = result
                        return result
                
                return None
            
            time.sleep_us(10)
        
        sm_obj.active(0)
        return None

    class _View:
        __slots__ = ('_p', '_i')
        
        def __init__(self, parent: "SR04"):
            self._p = parent
            self._i = None
        
        def _set(self, indices: list[int]) -> "SR04._View":
            self._i = indices
            return self

        def __getitem__(self, idx: int | slice) -> "SR04._View":
            if isinstance(idx, slice):
                selected = [self._i[i] for i in range(*idx.indices(len(self._i)))]
                return self._set(selected)
            else:
                return self._set([self._i[idx]])

        def __len__(self) -> int:
            return len(self._i)

        def reset_filter(self):
            for i in self._i:
                self._p._filters[i].reset()

        @property
        def measurement(self) -> list[bool]:
            return [self._p._measurement_enabled[i] for i in self._i]

        @measurement.setter
        def measurement(self, enable: bool | list[bool]) -> None:
            if isinstance(enable, bool):
                enables = [enable] * len(self._i)
            else:
                if len(enable) != len(self._i):
                    raise ValueError("list length must match number of sensors")
                enables = enable
            
            for i, e in zip(self._i, enables):
                was_enabled = self._p._measurement_enabled[i]
                self._p._measurement_enabled[i] = e
                
                if e and not was_enabled:
                    self._p._last_time[i] = time.ticks_us()
                    self._p._trigger_single(i)
                elif not e and was_enabled:
                    self._p._sms[i].active(0)

        @property
        def value(self) -> list[float | None]:
            any_continuous = any(self._p._measurement_enabled[i] for i in self._i)
            
            if any_continuous:
                return [self._p._pending_results[i] for i in self._i]
            
            if len(self._i) == 1:
                return [self._p._measure_single(self._i[0])]
            else:
                self._p._trigger_all()
                results = self._p._read_all()
                return [results[i] for i in self._i]

        @property
        def last(self) -> list[float]:
            return [self._p._last_m[i] for i in self._i]

        @property
        def temperature(self) -> list[float]:
            return [self._p._temp_c[i] for i in self._i]

        @temperature.setter
        def temperature(self, temp_c: float | list[float]):
            if isinstance(temp_c, (int, float)):
                if not (-40.0 <= temp_c <= 85.0):
                    raise ValueError("Temperature must be between -40°C and +85°C")
                for i in self._i:
                    self._p._temp_c[i] = float(temp_c)
            else:
                if len(temp_c) != len(self._i):
                    raise ValueError("list length must match number of sensors")
                for i, t in zip(self._i, temp_c):
                    if not (-40.0 <= t <= 85.0):
                        raise ValueError("Temperature must be between -40°C and +85°C")
                    self._p._temp_c[i] = float(t)

        @property
        def filter(self) -> list[dict]:
            return [
                {
                    'R': int(round(self._p._filters[i]._R * 10000.0)),
                    'Q': int(round(self._p._filters[i]._Q * 10000.0))
                }
                for i in self._i
            ]

        @filter.setter
        def filter(self, params: dict):
            if not isinstance(params, dict):
                raise TypeError("Filter parameters must be a dictionary")
            R = params.get('R')
            Q = params.get('Q')
            for i in self._i:
                if R is not None:
                    if not (10 <= R <= 100):
                        raise ValueError("R (measurement noise) must be in range 10-100")
                    self._p._filters[i]._R = float(R) / 10000.0
                if Q is not None:
                    if not (1 <= Q <= 10):
                        raise ValueError("Q (process noise) must be in range 1-10")
                    self._p._filters[i]._Q = float(Q) / 10000.0

        @property
        def filter_states(self) -> list[dict]:
            return [
                {
                    'position': self._p._filters[i]._x,
                    'velocity': self._p._filters[i]._v,
                    'covariance': [row[:] for row in self._p._filters[i]._P],
                    'measurement_noise': int(round(self._p._filters[i]._R * 10000.0)),
                    'process_noise': int(round(self._p._filters[i]._Q * 10000.0))
                }
                for i in self._i
            ]

        @property
        def callback(self) -> list[callable | None]:
            return [self._p._user_callbacks[i] for i in self._i]

        @callback.setter
        def callback(self, fn: callable | list[callable] | None):
            if callable(fn) or fn is None:
                for i in self._i:
                    self._p._user_callbacks[i] = fn
            else:
                if len(fn) != len(self._i):
                    raise ValueError("list length must match number of sensors")
                for i, cb in zip(self._i, fn):
                    if not (callable(cb) or cb is None):
                        raise TypeError("Each callback must be callable or None")
                    self._p._user_callbacks[i] = cb

        @property
        def sm_ids(self) -> list[int]:
            return [self._p._sm_ids[i] for i in self._i]
