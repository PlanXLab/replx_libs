__version__ = "1.0.0"
__author__ = "PlanX Lab Development Team"

from .nb_impl import (
    Q_ACC, Q_GYRO, Q_EULER, Q_QUAT, Q_LINACC,
    U_MS2, U_RAD_S, U_RAD, U_NONE,
    F_SENSOR, F_ENU,
    OK, BUS_ERR,
    ChannelInfo, Sample, NBAdapterBase
)


class MPU6050NB(NBAdapterBase):
    __slots__ = ("dev", "_cfg", "_last_ts_us")

    def __init__(self, dev, *,
                 include_euler=True,
                 include_quat=True,
                 include_linacc=True,
                 include_extras=False):
        self.dev = dev
        self._cfg = {
            "include_euler": bool(include_euler),
            "include_quat":  bool(include_quat),
            "include_linacc": bool(include_linacc),
            "include_extras": bool(include_extras),
        }
        self._last_ts_us = None
        super().__init__()

    def channels(self):
        ch = [
            ChannelInfo(Q_ACC,   U_MS2,   F_SENSOR, (3,), nominal_rate_hz=0.0),
            ChannelInfo(Q_GYRO,  U_RAD_S, F_SENSOR, (3,), nominal_rate_hz=0.0),
        ]
        if self._cfg["include_euler"]:
            ch.append(ChannelInfo(Q_EULER, U_RAD,  F_ENU, (3,), nominal_rate_hz=0.0))
        if self._cfg["include_quat"]:
            ch.append(ChannelInfo(Q_QUAT, U_NONE, F_ENU, (4,), nominal_rate_hz=0.0))
        if self._cfg["include_linacc"]:
            ch.append(ChannelInfo(Q_LINACC, U_MS2, F_ENU, (3,), nominal_rate_hz=0.0))
        return tuple(ch)

    def configure(self, **kw):
        if "include_euler" in kw:
            self._cfg["include_euler"] = bool(kw["include_euler"])
        if "include_quat" in kw:
            self._cfg["include_quat"]  = bool(kw["include_quat"])
        if "include_linacc" in kw:
            self._cfg["include_linacc"] = bool(kw["include_linacc"])
        if "include_extras" in kw:
            self._cfg["include_extras"] = bool(kw["include_extras"])

    def _update_impl(self):
        status_bits = OK
        src_str = "mpu6050" if self._cfg["include_extras"] else ""

        try:
            ax, ay, az = self.dev.accel
            gx, gy, gz = self.dev.gyro
        except Exception:
            try:
                if getattr(self.dev, "_i2c", None):
                    self._stats["last_err"] = BUS_ERR if getattr(self.dev._i2c, "last_error", 0) != 0 else OK
            except Exception:
                pass
            raise

        try:
            if getattr(self.dev, "_i2c", None) and getattr(self.dev._i2c, "last_error", 0) != 0:
                status_bits |= BUS_ERR
        except Exception:
            pass

        self._emit(Sample(Q_ACC, U_MS2, F_SENSOR, (3,), (ax, ay, az), status_bits, src_str))
        self._emit(Sample(Q_GYRO, U_RAD_S, F_SENSOR, (3,), (gx, gy, gz), status_bits, src_str))

        if self._cfg["include_quat"]:
            try:
                qw, qx, qy, qz = self.dev.quat
                self._emit(Sample(Q_QUAT, U_NONE, F_ENU, (4,), (qw, qx, qy, qz), status_bits, src_str))
            except Exception:
                pass

        if self._cfg["include_euler"]:
            try:
                roll, pitch, yaw = self.dev.euler
                self._emit(Sample(Q_EULER, U_RAD, F_ENU, (3,), (roll, pitch, yaw), status_bits, src_str))
            except Exception:
                pass

        if self._cfg["include_linacc"]:
            try:
                lax, lay, laz = self.dev.linear
                self._emit(Sample(Q_LINACC, U_MS2, F_ENU, (3,), (lax, lay, laz), status_bits, src_str))
            except Exception:
                pass

        return True
