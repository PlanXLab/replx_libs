__version__ = "1.1.0"
__author__  = "PlanX Lab Development Team"

from .nb_impl import NBAdapterBase
from . import nb_impl as _N
from . import math


class AS5600NB(NBAdapterBase):
    """
    Non-blocking adapter for AS5600 12-bit magnetic rotary encoder.
    
    Provides asynchronous access to angle, angular velocity, and multi-turn data
    through a channel-based subscription system.
    
    Channels:
        Q_ANGLE (U_RAD): Absolute angle in radians [0, 2π)
        Q_ANGVEL (U_RAD_S): Angular velocity in rad/s
        Q_TURN (U_NONE): Multi-turn counter (accumulated_turns, path_turns)
    
    Status Bits:
        NO_SIGNAL: No magnet detected
        CALIBRATING: Weak magnetic field
        SATURATED: Magnetic field too strong
        BUS_ERR: I2C communication error
    
    Example:
        >>> from ext import AS5600, AS5600NB
        >>> dev = AS5600(scl=5, sda=4)
        >>> nb = AS5600NB(dev, filtered=True)
        >>> 
        >>> def on_angle(sample):
        ...     print(f"Angle: {sample.value:.3f} rad")
        >>> 
        >>> nb.subscribe(nb.Q_ANGLE, on_angle)
        >>> nb.update_once()  # Call periodically
    
    Args:
        dev: AS5600 device instance
        filtered: Enable EMA/lowpass filtering (default: True)
        include_turn: Include multi-turn channel (default: True)
        include_extras: Include status info in src field (default: False)
    """
    Q_ANGLE   = _N.Q_ANGLE
    Q_ANGVEL  = _N.Q_ANGVEL
    Q_TURN    = _N.Q_TURN

    U_RAD     = _N.U_RAD
    U_RAD_S   = _N.U_RAD_S
    U_NONE    = _N.U_NONE

    F_SENSOR  = _N.F_SENSOR

    OK           = _N.OK
    CALIBRATING  = _N.CALIBRATING
    SATURATED    = _N.SATURATED
    NO_SIGNAL    = _N.NO_SIGNAL
    BUS_ERR      = _N.BUS_ERR

    ChannelInfo = _N.ChannelInfo
    Sample      = _N.Sample

    __slots__ = ("dev", "_cfg")

    def __init__(self, dev, *, 
                 filtered=True,
                 include_turn=True,
                 include_extras=False):
        self.dev = dev
        self._cfg = {
            "filtered": bool(filtered),
            "include_turn": bool(include_turn),
            "include_extras": bool(include_extras),
        }
        super().__init__()

    def channels(self):
        ch = [
            self.ChannelInfo(self.Q_ANGLE, self.U_RAD, self.F_SENSOR, (), nominal_rate_hz=0.0, range=(0.0, 2.0 * math.pi)),
            self.ChannelInfo(self.Q_ANGVEL, self.U_RAD_S, self.F_SENSOR, (), nominal_rate_hz=0.0, range=None),
        ]
        if self._cfg.get("include_turn", True):
            ch.append(self.ChannelInfo(self.Q_TURN, self.U_NONE, self.F_SENSOR, (), nominal_rate_hz=0.0, range=None))
        return tuple(ch)

    def configure(self, **kw):
        if "filtered" in kw:
            self._cfg["filtered"] = bool(kw["filtered"])
        if "include_turn" in kw:
            self._cfg["include_turn"] = bool(kw["include_turn"])
        if "include_extras" in kw:
            self._cfg["include_extras"] = bool(kw["include_extras"])

    def _update_impl(self):
        """
        Update sensor readings and emit samples for all configured channels.
        
        Checks magnetic field status and sets appropriate status bits:
        - NO_SIGNAL: No magnet detected
        - CALIBRATING: Weak magnetic field
        - SATURATED: Magnetic field too strong
        - BUS_ERR: I2C communication error
        
        Returns:
            bool: True if update successful, False on error
        """
        self.dev.reset_cache()

        status_bits = self.OK
        src_str = ""

        # Check magnetic field status
        try:
            mag_status = self.dev.status()
            if mag_status == self.dev.STATUS_NO_MAGNET:
                status_bits |= self.NO_SIGNAL
            elif mag_status == self.dev.STATUS_WEAK_MAGNET:
                status_bits |= self.CALIBRATING
            elif mag_status == self.dev.STATUS_STRONG_MAGNET:
                status_bits |= self.SATURATED
            # STATUS_FIELD_RANGE and STATUS_NORMAL don't set status bits
        except Exception:
            status_bits |= self.BUS_ERR

        # Read sensor values
        a = self.dev.angle(soft_zero=True, filtered=self._cfg["filtered"])
        v = self.dev.velocity(filtered=self._cfg["filtered"])

        t_val = None
        if self._cfg.get("include_turn", True):
            t_val = self.dev.turn(soft_zero=True, filtered=self._cfg["filtered"])

        # Optional: Include detailed status in src field
        if self._cfg.get("include_extras", False):
            try:
                st = self.dev.status()
                agc = self.dev.agc()
                mag = self.dev.magnitude()
                src_str = "as5600:st=%d,agc=%d,mag=%d" % (st, agc, mag)
            except Exception:
                src_str = ""

        # Check I2C bus error
        try:
            if getattr(self.dev, "_i2c", None) and getattr(self.dev._i2c, "last_error", 0) != 0:
                status_bits |= self.BUS_ERR
        except Exception:
            pass

        self._emit(self.Sample(self.Q_ANGLE,  self.U_RAD,   self.F_SENSOR, (), a, status_bits, src_str))
        self._emit(self.Sample(self.Q_ANGVEL, self.U_RAD_S, self.F_SENSOR, (), v, status_bits, src_str))
        if t_val is not None:
            self._emit(self.Sample(self.Q_TURN,   self.U_NONE,  self.F_SENSOR, (), t_val, status_bits, src_str))

        return True
