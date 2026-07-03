# @package: button
# @version: 2.2
# @type: device-std
# @category: input
# @sensor_type: C
# @interface: GPIO
# @depends: dio
# @platforms: *
# @tags: button, input, gpio, gesture, click, long_press
# @author: PlanXLab Development Team

from micropython import const
import time

from dio import Din

_STATE_IDLE              = const(0)
_STATE_PRESSED           = const(1)
_STATE_WAIT_RELEASE      = const(2)
_STATE_WAIT_DOUBLE       = const(3)
_STATE_DOUBLE_CLK_READY  = const(4)

_DEFAULT_DEBOUNCE_MS       = const(5)
_DEFAULT_LONG_PRESS_MS     = const(400)
_DEFAULT_DOUBLE_CLICK_MS   = const(200)

ACTIVE_HIGH = const(1)
ACTIVE_LOW  = const(0)

_EVT_ALL     = const(0)
_EVT_PRESS   = const(1)
_EVT_RELEASE = const(2)
_EVT_CLICK   = const(3)
_EVT_DBCLICK = const(4)
_EVT_LPRESS  = const(5)


class Button:
    ALL     = _EVT_ALL
    PRESS   = _EVT_PRESS
    RELEASE = _EVT_RELEASE
    CLICK   = _EVT_CLICK
    DBCLICK = _EVT_DBCLICK
    LPRESS  = _EVT_LPRESS
    
    def __init__(
        self,
        pins: int | list[int] | tuple[int, ...],
        *,
        active_high: bool = True,
        pull: int | None = None,
        debounce_ms: int = _DEFAULT_DEBOUNCE_MS,
        long_press_ms: int = _DEFAULT_LONG_PRESS_MS,
        double_click_gap_ms: int = _DEFAULT_DOUBLE_CLICK_MS
    ):
        if isinstance(pins, int):
            pins = [pins]
        self._pins = list(pins)
        n = len(self._pins)
        
        self._active_high = bool(active_high)
        self._din = Din(self._pins)
        
        if pull is None:
            pull = Din.PULL_DOWN if active_high else Din.PULL_UP
        self._din.set_pull_all(pull)
        
        self._debounce_ms = debounce_ms
        self._long_press_ms = long_press_ms
        self._double_click_gap_ms = double_click_gap_ms
        
        self._states = [_STATE_IDLE] * n
        self._press_times = [0] * n
        self._release_times = [0] * n
        self._last_click_times = [0] * n
        self._long_press_fired = [False] * n
        
        self._on_press = [None] * n
        self._on_release = [None] * n
        self._on_click = [None] * n
        self._on_double_click = [None] * n
        self._on_long_press = [None] * n
        self._edge_callbacks = [self._make_edge_callback(i) for i in range(n)]
        self._events = []
        
        self._running = False
        self._view = Button._View(self)
    
    def __enter__(self) -> "Button":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.deinit()
    
    def __len__(self) -> int:
        return len(self._pins)
    
    def __getitem__(self, idx: int | slice) -> "_View":
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(len(self._pins))))
            return self._view._set(indices)
        elif isinstance(idx, int):
            if idx < 0:
                idx += len(self._pins)
            if not (0 <= idx < len(self._pins)):
                raise IndexError("Button index out of range")
            return self._view._set([idx])
        else:
            raise TypeError("Index must be int or slice")
    
    def deinit(self) -> None:
        self.stop()
        self._din.deinit()
    
    @property
    def pins(self) -> list[int]:
        return self._pins.copy()
    
    @property
    def active_high(self) -> bool:
        return self._active_high
    
    @property
    def debounce_ms(self) -> int:
        return self._debounce_ms
    
    @debounce_ms.setter
    def debounce_ms(self, ms: int) -> None:
        self._debounce_ms = ms
        self._din.set_debounce_all(ms * 1000)
    
    @property
    def long_press_ms(self) -> int:
        return self._long_press_ms
    
    @long_press_ms.setter
    def long_press_ms(self, ms: int) -> None:
        self._long_press_ms = ms
    
    @property
    def double_click_gap_ms(self) -> int:
        return self._double_click_gap_ms
    
    @double_click_gap_ms.setter
    def double_click_gap_ms(self, ms: int) -> None:
        self._double_click_gap_ms = ms
    
    def _get_pressed(self, idx: int) -> bool:
        raw = self._din.read(idx)
        return bool(raw) if self._active_high else not bool(raw)

    def is_pressed(self, idx: int = 0) -> bool:
        return self._get_pressed(idx)

    def is_released(self, idx: int = 0) -> bool:
        return not self._get_pressed(idx)

    def _fire_callback(self, cb, idx: int) -> None:
        if cb is None:
            return
        try:
            cb(idx)
        except TypeError:
            try:
                cb()
            except Exception:
                pass
        except Exception:
            pass
    
    def _make_edge_callback(self, idx: int):
        def _callback(_pin_num, rising):
            self._handle_edge_idx(idx, rising)
        return _callback
    
    def _uses_gesture(self, idx: int) -> bool:
        return (self._on_click[idx] is not None or
                self._on_double_click[idx] is not None or
                self._on_long_press[idx] is not None)
    
    def _edge_for(self, idx: int) -> int:
        if self._uses_gesture(idx):
            return Din.CB_BOTH
        
        edge = 0
        if self._on_press[idx] is not None:
            edge |= Din.CB_RISING if self._active_high else Din.CB_FALLING
        if self._on_release[idx] is not None:
            edge |= Din.CB_FALLING if self._active_high else Din.CB_RISING
        return edge
    
    def _configure_irq(self, idx: int) -> None:
        self._din.irq(idx, None)
        edge = self._edge_for(idx)
        if edge:
            self._din.irq(idx, self._edge_callbacks[idx], trigger=edge,
                          debounce_us=self._debounce_ms * 1000, hard=False)
    
    def _set_callback(self, target, idx: int, callback) -> None:
        target[idx] = callback
        if self._running:
            self._configure_irq(idx)
    
    def _handle_edge_idx(self, idx: int, rising: bool) -> None:
        is_press = (rising if self._active_high else not rising)
        
        if not self._uses_gesture(idx):
            self._states[idx] = _STATE_PRESSED if is_press else _STATE_IDLE
            if is_press:
                self._fire_callback(self._on_press[idx], idx)
            else:
                self._fire_callback(self._on_release[idx], idx)
            return
        
        now = time.ticks_ms()
        if is_press:
            if self._states[idx] == _STATE_WAIT_DOUBLE:
                gap = time.ticks_diff(now, self._last_click_times[idx])
                if gap <= self._double_click_gap_ms:
                    self._states[idx] = _STATE_WAIT_RELEASE
                else:
                    self._fire_callback(self._on_click[idx], idx)
                    self._states[idx] = _STATE_PRESSED
            else:
                self._states[idx] = _STATE_PRESSED
            self._press_times[idx] = now
            self._long_press_fired[idx] = False
            self._fire_callback(self._on_press[idx], idx)
        else:
            self._release_times[idx] = now
            self._fire_callback(self._on_release[idx], idx)
            
            if self._on_long_press[idx] is not None:
                if time.ticks_diff(now, self._press_times[idx]) >= self._long_press_ms:
                    self._long_press_fired[idx] = True
                    self._states[idx] = _STATE_IDLE
                    self._fire_callback(self._on_long_press[idx], idx)
                    return
            
            if self._states[idx] == _STATE_WAIT_RELEASE:
                self._states[idx] = _STATE_IDLE
                self._fire_callback(self._on_double_click[idx], idx)
                return
            
            if not self._long_press_fired[idx]:
                if self._on_double_click[idx] is None:
                    self._states[idx] = _STATE_IDLE
                    self._fire_callback(self._on_click[idx], idx)
                else:
                    self._last_click_times[idx] = now
                    self._states[idx] = _STATE_WAIT_DOUBLE
    
    def start(self) -> None:
        if self._running:
            return
        
        self._running = True
        for i in range(len(self._pins)):
            self._states[i] = _STATE_IDLE
            self._configure_irq(i)
    
    def stop(self) -> None:
        if not self._running:
            return
        
        self._running = False
        for i in range(len(self._pins)):
            self._din.irq(i, None)
    
    def _update_single(self, idx: int, now: int) -> str | None:
        is_pressed = self._get_pressed(idx)
        
        if self._states[idx] == _STATE_IDLE:
            if is_pressed:
                self._press_times[idx] = now
                self._long_press_fired[idx] = False
                self._states[idx] = _STATE_PRESSED
                self._fire_callback(self._on_press[idx], idx)
                return 'press'
        
        elif self._states[idx] == _STATE_PRESSED:
            if not is_pressed:
                self._release_times[idx] = now
                self._fire_callback(self._on_release[idx], idx)
                
                if self._long_press_fired[idx]:
                    self._states[idx] = _STATE_IDLE
                    return 'release'
                
                self._last_click_times[idx] = now
                self._states[idx] = _STATE_WAIT_DOUBLE
                return 'release'
            else:
                if not self._long_press_fired[idx]:
                    if time.ticks_diff(now, self._press_times[idx]) >= self._long_press_ms:
                        self._long_press_fired[idx] = True
                        self._fire_callback(self._on_long_press[idx], idx)
                        return 'long_press'
        
        elif self._states[idx] == _STATE_WAIT_DOUBLE:
            if is_pressed:
                gap = time.ticks_diff(now, self._last_click_times[idx])
                if gap <= self._double_click_gap_ms:
                    self._press_times[idx] = now
                    self._long_press_fired[idx] = False
                    self._states[idx] = _STATE_DOUBLE_CLK_READY
                    self._fire_callback(self._on_press[idx], idx)
                    return 'press'
                else:
                    self._fire_callback(self._on_click[idx], idx)
                    self._press_times[idx] = now
                    self._long_press_fired[idx] = False
                    self._states[idx] = _STATE_PRESSED
                    self._fire_callback(self._on_press[idx], idx)
                    return 'click'
            else:
                if time.ticks_diff(now, self._last_click_times[idx]) > self._double_click_gap_ms:
                    self._states[idx] = _STATE_IDLE
                    self._fire_callback(self._on_click[idx], idx)
                    return 'click'
        
        elif self._states[idx] == _STATE_WAIT_RELEASE:
            if not is_pressed:
                self._states[idx] = _STATE_IDLE
        
        elif self._states[idx] == _STATE_DOUBLE_CLK_READY:
            self._states[idx] = _STATE_WAIT_RELEASE
            self._fire_callback(self._on_double_click[idx], idx)
            return 'double_click'
        
        return None
    
    def update(self, type: int = _EVT_ALL) -> list:
        results = self._events
        results.clear()
        n = len(self._pins)
        now = time.ticks_ms()

        if type == _EVT_ALL:
            for i in range(n):
                event = self._update_single(i, now)
                if event == 'press':
                    for j in range(n):
                        if j != i and self._states[j] == _STATE_WAIT_DOUBLE:
                            self._states[j] = _STATE_IDLE
                            self._fire_callback(self._on_click[j], j)
                            results.append((j, 'click'))
                if event:
                    results.append((i, event))
            return results

        # Specific filter — returns list[int] (indices only)
        if type == _EVT_PRESS:
            target = 'press'
        elif type == _EVT_RELEASE:
            target = 'release'
        elif type == _EVT_CLICK:
            target = 'click'
        elif type == _EVT_DBCLICK:
            target = 'double_click'
        else:
            target = 'long_press'

        for i in range(n):
            event = self._update_single(i, now)
            if event == 'press':
                for j in range(n):
                    if j != i and self._states[j] == _STATE_WAIT_DOUBLE:
                        self._states[j] = _STATE_IDLE
                        self._fire_callback(self._on_click[j], j)
                        if type == _EVT_CLICK:
                            results.append(j)
            if event == target:
                results.append(i)
        return results
    
    def wait_for_press(self, idx: int = 0, timeout_ms: int = 0) -> bool:
        if timeout_ms <= 0:
            while not self._get_pressed(idx):
                pass
            return True
        
        start = time.ticks_ms()
        while not self._get_pressed(idx):
            if time.ticks_diff(time.ticks_ms(), start) >= timeout_ms:
                return False
        return True
    
    def wait_for_release(self, idx: int = 0, timeout_ms: int = 0) -> bool:
        if timeout_ms <= 0:
            while self._get_pressed(idx):
                pass
            return True
        
        start = time.ticks_ms()
        while self._get_pressed(idx):
            if time.ticks_diff(time.ticks_ms(), start) >= timeout_ms:
                return False
        return True
    
    def wait_for_click(self, idx: int = 0, timeout_ms: int = 0) -> bool:
        start = time.ticks_ms()
        
        if timeout_ms <= 0:
            if not self.wait_for_press(idx, 0):
                return False
            return self.wait_for_release(idx, 0)
        
        if not self.wait_for_press(idx, timeout_ms):
            return False
        
        elapsed = time.ticks_diff(time.ticks_ms(), start)
        remaining = max(0, timeout_ms - elapsed)
        return self.wait_for_release(idx, remaining)
    
    class _View:
        __slots__ = ('_p', '_i')
        
        def __init__(self, parent: "Button"):
            self._p = parent
            self._i = None
        
        def _set(self, indices: list[int]) -> "Button._View":
            self._i = tuple(indices)
            return self
        
        def __len__(self) -> int:
            return len(self._i)
        
        def __getitem__(self, idx: int | slice) -> "Button._View":
            if isinstance(idx, slice):
                self._i = tuple(self._i[j] for j in range(*idx.indices(len(self._i))))
            else:
                self._i = (self._i[idx],)
            return self
        
        @property
        def pin(self) -> list[int]:
            return [self._p._pins[i] for i in self._i]
        
        @property
        def pressed(self) -> list[bool]:
            return [self._p._get_pressed(i) for i in self._i]
        
        @property
        def released(self) -> list[bool]:
            return [not self._p._get_pressed(i) for i in self._i]
        
        def is_pressed(self, idx: int = 0) -> bool:
            return self._p._get_pressed(self._i[idx])

        def is_released(self, idx: int = 0) -> bool:
            return not self._p._get_pressed(self._i[idx])
        
        @property
        def on_press(self) -> list:
            return [self._p._on_press[i] for i in self._i]
        
        @on_press.setter
        def on_press(self, callback) -> None:
            if isinstance(callback, (list, tuple)):
                if len(callback) != len(self._i):
                    raise ValueError("Callback list length must match")
                for i, cb in zip(self._i, callback):
                    self._p._set_callback(self._p._on_press, i, cb)
            else:
                for i in self._i:
                    self._p._set_callback(self._p._on_press, i, callback)
        
        @property
        def on_release(self) -> list:
            return [self._p._on_release[i] for i in self._i]
        
        @on_release.setter
        def on_release(self, callback) -> None:
            if isinstance(callback, (list, tuple)):
                if len(callback) != len(self._i):
                    raise ValueError("Callback list length must match")
                for i, cb in zip(self._i, callback):
                    self._p._set_callback(self._p._on_release, i, cb)
            else:
                for i in self._i:
                    self._p._set_callback(self._p._on_release, i, callback)
        
        @property
        def on_click(self) -> list:
            return [self._p._on_click[i] for i in self._i]
        
        @on_click.setter
        def on_click(self, callback) -> None:
            if isinstance(callback, (list, tuple)):
                if len(callback) != len(self._i):
                    raise ValueError("Callback list length must match")
                for i, cb in zip(self._i, callback):
                    self._p._set_callback(self._p._on_click, i, cb)
            else:
                for i in self._i:
                    self._p._set_callback(self._p._on_click, i, callback)
        
        @property
        def on_double_click(self) -> list:
            return [self._p._on_double_click[i] for i in self._i]
        
        @on_double_click.setter
        def on_double_click(self, callback) -> None:
            if isinstance(callback, (list, tuple)):
                if len(callback) != len(self._i):
                    raise ValueError("Callback list length must match")
                for i, cb in zip(self._i, callback):
                    self._p._set_callback(self._p._on_double_click, i, cb)
            else:
                for i in self._i:
                    self._p._set_callback(self._p._on_double_click, i, callback)
        
        @property
        def on_long_press(self) -> list:
            return [self._p._on_long_press[i] for i in self._i]
        
        @on_long_press.setter
        def on_long_press(self, callback) -> None:
            if isinstance(callback, (list, tuple)):
                if len(callback) != len(self._i):
                    raise ValueError("Callback list length must match")
                for i, cb in zip(self._i, callback):
                    self._p._set_callback(self._p._on_long_press, i, cb)
            else:
                for i in self._i:
                    self._p._set_callback(self._p._on_long_press, i, callback)
        
        def update(self, type: int = _EVT_ALL) -> list:
            p = self._p
            results = p._events
            results.clear()
            indices = self._i
            n = len(indices)
            now = time.ticks_ms()

            if type == _EVT_ALL:
                for k in range(n):
                    i = indices[k]
                    event = p._update_single(i, now)
                    if event == 'press':
                        for m in range(n):
                            j = indices[m]
                            if j != i and p._states[j] == _STATE_WAIT_DOUBLE:
                                p._states[j] = _STATE_IDLE
                                p._fire_callback(p._on_click[j], j)
                                results.append((j, 'click'))
                    if event:
                        results.append((i, event))
                return results

            if type == _EVT_PRESS:
                target = 'press'
            elif type == _EVT_RELEASE:
                target = 'release'
            elif type == _EVT_CLICK:
                target = 'click'
            elif type == _EVT_DBCLICK:
                target = 'double_click'
            else:
                target = 'long_press'

            for k in range(n):
                i = indices[k]
                event = p._update_single(i, now)
                if event == 'press':
                    for m in range(n):
                        j = indices[m]
                        if j != i and p._states[j] == _STATE_WAIT_DOUBLE:
                            p._states[j] = _STATE_IDLE
                            p._fire_callback(p._on_click[j], j)
                            if type == _EVT_CLICK:
                                results.append(j)
                if event == target:
                    results.append(i)
            return results


