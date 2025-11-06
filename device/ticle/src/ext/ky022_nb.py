__version__ = "1.0.0"
__author__ = "PlanX Lab Development Team"

from .nb_impl import (
    Q_IR_CODE, 
    U_NONE, 
    F_SENSOR,
    OK, BUS_ERR,
    Sample, ChannelInfo, NBAdapterBase, 
)


class KY022NB(NBAdapterBase):
    __slots__ = ("dev", "_max_drain_per_update", "_emit_repeat", "_proto_name", "_include_extras")

    def __init__(self, dev, *, max_drain_per_update=4, emit_repeat=None, include_extras=False):
        self.dev = dev
        super().__init__()
        self._max_drain_per_update = int(max(1, max_drain_per_update))
        self._emit_repeat = emit_repeat
        self._include_extras = bool(include_extras)

        self._proto_name = {
            getattr(self.dev, "PROTOCOL_NEC_8", 1):      "NEC8",
            getattr(self.dev, "PROTOCOL_NEC_16", 2):     "NEC16",
            getattr(self.dev, "PROTOCOL_SAMSUNG", 3):    "SAMSUNG",
            getattr(self.dev, "PROTOCOL_SIRC12", 4):     "SIRC12",
            getattr(self.dev, "PROTOCOL_SIRC15", 5):     "SIRC15",
            getattr(self.dev, "PROTOCOL_SIRC20", 6):     "SIRC20",
            getattr(self.dev, "PROTOCOL_RC5", 7):        "RC5",
            getattr(self.dev, "PROTOCOL_RC6", 8):        "RC6",
            getattr(self.dev, "PROTOCOL_PANA", 9):       "PANA",
            getattr(self.dev, "PROTOCOL_CARRIER40", 10): "CARRIER40",
            getattr(self.dev, "PROTOCOL_CARRIER84", 11): "CARRIER84",
            getattr(self.dev, "PROTOCOL_CARRIER128", 12):"CARRIER128",
            getattr(self.dev, "PROTOCOL_HVAC_NEC", 13):  "HVAC_NEC",
        }

    def channels(self):
        return (ChannelInfo(Q_IR_CODE, U_NONE, F_SENSOR, (), nominal_rate_hz=0.0),)

    def _update_impl(self):
        emitted = 0
        for _ in range(self._max_drain_per_update):
            evt = self.dev.get(block=False)
            if evt is None:
                break

            try:
                cmd, addr, ext = evt
            except Exception:
                self._stats["last_err"] = BUS_ERR
                continue

            is_repeat = 0

            if self._emit_repeat is False and is_repeat:
                continue

            if self._include_extras:
                src = "proto=%s,addr=0x%04X,ext=0x%X,repeat=%d" % (
                    self._proto_name.get(getattr(self.dev, "_proto", 0), "UNK"),
                    int(addr) & 0xFFFF,
                    int(ext) & 0xFFFFFFFF,
                    is_repeat
                )
            else:
                src = ""

            sample = Sample(Q_IR_CODE, U_NONE, F_SENSOR, (), int(cmd) & 0xFF, OK, src)
            self._emit(sample)
            emitted += 1

        return emitted > 0

    def configure(self, **kw):
        if "max_drain_per_update" in kw:
            self._max_drain_per_update = int(max(1, kw["max_drain_per_update"]))
        if "emit_repeat" in kw:
            v = kw["emit_repeat"]
            if v is None or isinstance(v, bool):
                self._emit_repeat = v
        if "include_extras" in kw:
            self._include_extras = bool(kw["include_extras"])
