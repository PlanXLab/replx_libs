__version__ = "1.0.0"
__author__ = "PlanX Lab Development Team"

from .nb_impl import (
    Q_DIST,
    U_M,
    F_SENSOR,
    OK, BUS_ERR, STALE,
    ChannelInfo, Sample, NBAdapterBase
)


class VL53L0XNB(NBAdapterBase):
    __slots__ = ("dev", "_cfg", "_last_ts_us")

    def __init__(self, dev, *, include_extras: bool = False):
        self.dev = dev
        self._cfg = {
            "include_extras": bool(include_extras),
        }
        self._last_ts_us = None
        super().__init__()

    def channels(self):
        return (
            ChannelInfo(Q_DIST, U_M, F_SENSOR, (), nominal_rate_hz=0.0, range=None),
        )

    def configure(self, **kw):
        if "include_extras" in kw:
            self._cfg["include_extras"] = bool(kw["include_extras"])

    def _update_impl(self):
        status_bits = OK
        src_str = "vl53l0x" if self._cfg["include_extras"] else ""

        try:
            if getattr(self.dev, "_i2c", None) and getattr(self.dev._i2c, "last_error", 0) != 0:
                status_bits |= BUS_ERR
        except Exception:
            pass

        try:
            dist_m = self.dev.read()
        except Exception:
            status_bits |= BUS_ERR

        if dist_m is None:
            prev = self._last.get(Q_DIST)
            if prev is not None:
                self._emit(Sample(Q_DIST, U_M, F_SENSOR, (), prev.value, status_bits | STALE, src_str))
            return True

        self._emit(Sample(Q_DIST, U_M, F_SENSOR, (), dist_m, status_bits, src_str))
        return True
