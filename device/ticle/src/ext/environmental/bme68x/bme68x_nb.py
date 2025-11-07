import utime
from ext.nb_impl import NBAdapterBase
from ext import nb_impl as _N

__version__ = "1.3.0"
__author__  = "PlanX Lab Development Team"


class BME68xNB(NBAdapterBase):
    Q_TEMP   = _N.Q_TEMP
    Q_PRESS  = _N.Q_PRESS
    Q_HUM    = _N.Q_HUM
    Q_GAS    = _N.Q_GAS
    Q_IAQ    = _N.Q_IAQ

    U_DEGC   = _N.U_DEGC
    U_RH     = _N.U_RH
    U_PA     = _N.U_PA
    U_OHM    = _N.U_OHM
    U_NONE   = _N.U_NONE

    F_SENSOR = _N.F_SENSOR

    OK      = _N.OK
    BUS_ERR = _N.BUS_ERR
    STALE   = _N.STALE

    ChannelInfo = _N.ChannelInfo
    Sample      = _N.Sample

    __slots__ = ("dev", "_cfg", "_sched", "_cache")

    def __init__(self, dev, *, include_iaq: bool = False, include_extras: bool = False):
        self.dev = dev
        self._cfg = {
            "include_iaq": bool(include_iaq),
            "include_extras": bool(include_extras),
        }

        period = int(getattr(self.dev, "gas_update_hint_ms", 3000))
        now = utime.ticks_ms()
        self._sched = {
            "period_ms": period,
            "next_ms": now,
        }

        self._cache = {
            "t": None, "p_pa": None, "h": None,
            "g": None, "iaq": None,
            "ts": 0,
        }

        super().__init__()

    def channels(self):
        ch = [
            self.ChannelInfo(self.Q_TEMP,  self.U_DEGC, self.F_SENSOR, (), nominal_rate_hz=0.0, range=(-40.0, 85.0)),
            self.ChannelInfo(self.Q_PRESS, self.U_PA,   self.F_SENSOR, (), nominal_rate_hz=0.0, range=None),
            self.ChannelInfo(self.Q_HUM,   self.U_RH,   self.F_SENSOR, (), nominal_rate_hz=0.0, range=(0.0, 100.0)),
        ]
        if self._cfg.get("include_iaq", False):
            ch.append(self.ChannelInfo(self.Q_GAS, self.U_OHM,  self.F_SENSOR, (), nominal_rate_hz=0.0, range=None))
            ch.append(self.ChannelInfo(self.Q_IAQ, self.U_NONE, self.F_SENSOR, (), nominal_rate_hz=0.0, range=(0, 500), resolution=1))
        return tuple(ch)

    def configure(self, **kw):
        if "include_iaq" in kw:
            self._cfg["include_iaq"] = bool(kw["include_iaq"])
        if "include_extras" in kw:
            self._cfg["include_extras"] = bool(kw["include_extras"])

    def _emit_env(self, t, p_pa, h, status_bits, src_str):
        self._emit(self.Sample(self.Q_TEMP,  self.U_DEGC, self.F_SENSOR, (), float(t),    status_bits, src_str))
        self._emit(self.Sample(self.Q_PRESS, self.U_PA,   self.F_SENSOR, (), float(p_pa), status_bits, src_str))
        self._emit(self.Sample(self.Q_HUM,   self.U_RH,   self.F_SENSOR, (), float(h),    status_bits, src_str))

    def _update_impl(self):
        status_bits = self.OK
        src_str = ""
        
        if self._cfg.get("include_extras", False):
            try:
                baseline = int(getattr(self.dev, "gas_baseline", 90000))
                period   = int(getattr(self.dev, "gas_update_hint_ms", self._sched["period_ms"]))
                age_ms   = utime.ticks_diff(utime.ticks_ms(), self._cache["ts"]) if self._cache["ts"] else -1
                src_str  = "bme68x:baseline=%d,period_ms=%d,age_ms=%d" % (baseline, period, int(age_ms))
            except Exception:
                src_str = "bme68x"

        if not self._cfg.get("include_iaq", False):
            try:
                try:
                    _ = self.dev._try_collect_ready_sample(assume_need_gas=False)
                except AttributeError:
                    pass

                t   = float(self.dev.temperature())
                p_h = float(self.dev.pressure())
                h   = float(self.dev.humidity())
                p_pa = p_h * 100.0
                self._emit_env(t, p_pa, h, status_bits, src_str)
                return True
            except Exception:
                self._stats["last_err"] = self.BUS_ERR
                return False

        try:
            period_now = int(getattr(self.dev, "gas_update_hint_ms", self._sched["period_ms"]))
            self._sched["period_ms"] = period_now

            now = utime.ticks_ms()
            if utime.ticks_diff(now, self._sched["next_ms"]) >= 0:
                out = self.dev.iaq_heuristics()  # 인자 없이: 디바이스의 현재 설정 사용
                self._sched["next_ms"] = utime.ticks_add(now, self._sched["period_ms"])

                if out is not None:
                    iaq, t, p_h, h, g = out
                    p_pa = float(p_h) * 100.0
                    self._cache.update({
                        "t": float(t), "p_pa": float(p_pa), "h": float(h),
                        "g": float(g), "iaq": int(iaq),
                        "ts": utime.ticks_ms(),
                    })

            if self._cache["ts"]:
                self._emit_env(self._cache["t"], self._cache["p_pa"], self._cache["h"], status_bits, src_str)
                if self._cache["g"] is not None:
                    self._emit(self.Sample(self.Q_GAS, self.U_OHM,  self.F_SENSOR, (), self._cache["g"], status_bits, src_str))
                if self._cache["iaq"] is not None:
                    self._emit(self.Sample(self.Q_IAQ, self.U_NONE, self.F_SENSOR, (), int(self._cache["iaq"]), status_bits, src_str))
            else:
                t = float(self.dev.temperature())
                p_h = float(self.dev.pressure())
                h = float(self.dev.humidity())
                p_pa = p_h * 100.0
                self._emit_env(t, p_pa, h, status_bits, src_str)

            return True

        except Exception:
            self._stats["last_err"] = self.BUS_ERR
            return False
