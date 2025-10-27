__version__ = "1.1.0"
__author__  = "PlanX Lab Development Team"

from .nb_impl import (
    NBAdapterBase, ChannelInfo, Sample,
    Q_BTN_STATE, Q_BTN_EVENT,
    U_NONE, F_SENSOR
)
from . import utime


class ButtonNB(NBAdapterBase):
    CLICKED        = 1
    DOUBLE_CLICKED = 2
    LONG_PRESSED   = 3
    PRESSED        = 4
    RELEASED       = 5

    def __init__(self, dev, *,
                 debounce_ms: int = 20,
                 double_click_window_ms: int = 300,
                 long_press_threshold_ms: int = 800,
                 emit_press_release: bool = True):
        super().__init__()
        self._btn = dev

        self._debounce_ms = int(debounce_ms)
        self._dc_ms       = int(double_click_window_ms)
        self._long_ms     = int(long_press_threshold_ms)
        self._emit_pr     = bool(emit_press_release)

        self._pressed          = bool(self._btn.pressed)
        self._last_edge_ms     = 0
        self._press_start_ms   = 0
        self._waiting_double   = False
        self._long_fired       = False
        self._dc_deadline_ms   = 0

        self._emit(Sample(Q_BTN_STATE, U_NONE, F_SENSOR, (), int(self._pressed), src="ButtonNB:init"))

    def channels(self):
        return (
            ChannelInfo(Q_BTN_STATE, U_NONE, F_SENSOR, ()),  # 0/1
            ChannelInfo(Q_BTN_EVENT, U_NONE, F_SENSOR, ()),  # CLICK/DBL/LONG/PRESSED/RELEASED
        )

    def set_options(self, *, debounce_ms: int = None,
                    double_click_window_ms: int = None,
                    long_press_threshold_ms: int = None,
                    emit_press_release: bool = None):
        if debounce_ms is not None:
            self._debounce_ms = int(debounce_ms)

        if double_click_window_ms is not None:
            self._dc_ms = int(double_click_window_ms)

        if long_press_threshold_ms is not None:
            self._long_ms = int(long_press_threshold_ms)

        if emit_press_release is not None:
            self._emit_pr = bool(emit_press_release)

    def _read_pressed(self) -> bool:
        return bool(self._btn.pressed)

    def _emit_state(self, val: bool):
        self._emit(Sample(Q_BTN_STATE, U_NONE, F_SENSOR, (), int(val), src="ButtonNB"))

    def _emit_event(self, ev_code: int):
        self._emit(Sample(Q_BTN_EVENT, U_NONE, F_SENSOR, (), int(ev_code), src="ButtonNB"))

    def _update_impl(self, now_ms=None):
        t = utime.ticks_ms() if now_ms is None else int(now_ms)

        cur = self._read_pressed()

        if not cur and self._waiting_double and utime.ticks_diff(self._dc_deadline_ms, t) <= 0:
            self._waiting_double = False
            self._emit_event(self.CLICKED)

        if cur == self._pressed:
            if self._pressed and not self._long_fired:
                if utime.ticks_diff(t, self._press_start_ms) >= self._long_ms:
                    self._long_fired = True
                    self._waiting_double = False
                    self._emit_event(self.LONG_PRESSED)
            return True

        if utime.ticks_diff(t, self._last_edge_ms) < self._debounce_ms:
            return True

        self._last_edge_ms = t
        prev = self._pressed
        self._pressed = cur
        self._emit_state(cur)

        if cur:  # PRESSED edge
            self._press_start_ms = t
            self._long_fired = False
            if self._emit_pr:
                self._emit_event(self.PRESSED)
        else:    # RELEASED edge
            press_dur = utime.ticks_diff(t, self._press_start_ms)
            if self._emit_pr:
                self._emit_event(self.RELEASED)

            if self._long_fired:
                self._long_fired = False
                self._waiting_double = False
            else:
                if press_dur >= self._debounce_ms and press_dur < self._long_ms:
                    if self._waiting_double and utime.ticks_diff(self._dc_deadline_ms, t) > 0:
                        self._waiting_double = False
                        self._emit_event(self.DOUBLE_CLICKED)
                    else:
                        self._waiting_double = True
                        self._dc_deadline_ms = utime.ticks_add(t, self._dc_ms)

        if self._pressed and not self._long_fired:
            if utime.ticks_diff(t, self._press_start_ms) >= self._long_ms:
                self._long_fired = True
                self._waiting_double = False
                self._emit_event(self.LONG_PRESSED)

        return True
