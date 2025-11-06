__version__ = "1.0.0"
__author__  = "PlanX Lab Development Team"

from .nb_impl import (
    Q_DIST,
    U_M,
    F_SENSOR,
    OK, STALE, OVERTIME,
    ChannelInfo, Sample, NBAdapterBase
)


class SR04NB(NBAdapterBase):
    __slots__ = ("dev", "_cfg")

    def __init__(self, dev, *, timeout_ms=50, include_extras=False):
        self.dev = dev
        self._cfg = {
            "timeout_ms": int(timeout_ms),
            "include_extras": bool(include_extras),
        }
        super().__init__()

    def channels(self):
        return (
            ChannelInfo(Q_DIST, U_M, F_SENSOR, (), nominal_rate_hz=0.0, range=None),
        )

    def configure(self, **kw):
        if "timeout_ms" in kw and kw["timeout_ms"] is not None:
            self._cfg["timeout_ms"] = int(kw["timeout_ms"])

        if "include_extras" in kw:
            self._cfg["include_extras"] = bool(kw["include_extras"])

    def _update_impl(self):
        status_bits = OK
        src_str = "sr04" if self._cfg["include_extras"] else ""

        m = self.dev.read(timeout_ms=self._cfg["timeout_ms"])

        if (m is None) or (m < 0.0):
            prev = self.last(Q_DIST)
            if prev is not None:
                self._emit(Sample(Q_DIST, U_M, F_SENSOR, (), prev.value, status_bits | STALE | OVERTIME, src_str))
            return True

        self._emit(Sample(Q_DIST, U_M, F_SENSOR, (), float(m), status_bits, src_str))
        return True
