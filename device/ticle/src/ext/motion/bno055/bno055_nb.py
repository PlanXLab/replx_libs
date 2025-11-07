from ext.nb_impl import (
    Q_ACC, Q_GYRO, Q_MAG, Q_EULER, Q_QUAT,  Q_LINACC, Q_GRAV,
    U_MS2, U_RAD_S, U_UT, U_RAD, U_NONE, U_DEGC,
    F_SENSOR, F_ENU,
    OK, CALIBRATING, BUS_ERR,
    ChannelInfo, Sample, NBAdapterBase
)

__version__ = "1.0.0"
__author__ = "PlanX Lab Development Team"


class BNO055NB(NBAdapterBase):
    __slots__ = ("dev", "_include_extras")

    def __init__(self, dev, *, include_extras=False):
        self.dev = dev
        self._include_extras = bool(include_extras)
        super().__init__() 

    def channels(self):
        return (
            ChannelInfo(Q_ACC, U_MS2, F_SENSOR, (3,)),
            ChannelInfo(Q_GYRO, U_RAD_S, F_SENSOR, (3,)),
            ChannelInfo(Q_MAG, U_UT, F_SENSOR, (3,)),
            ChannelInfo(Q_EULER, U_RAD, F_ENU, (3,)),
            ChannelInfo(Q_QUAT, U_NONE, F_ENU, (4,)),
            ChannelInfo(Q_LINACC, U_MS2, F_SENSOR, (3,)),
            ChannelInfo(Q_GRAV, U_MS2, F_SENSOR, (3,)),
        )

    def _update_impl(self):
        status_bits = OK
        src_str = ""

        try:
            diag = self.dev.diagnostics
            sys_, gyr, acc, mag = diag["calib"]
            if (sys_ < 3) or (gyr < 3) or (acc < 3) or (mag < 3):
                status_bits |= CALIBRATING
                
            if self._include_extras:
                src_str = "bno055:sys=%d,gyr=%d,acc=%d,mag=%d,stat=%d,err=%d" % (
                    sys_, gyr, acc, mag, diag["sys_stat"], diag["sys_err"]
                )
        except Exception:
            pass

        try:
            if getattr(self.dev, "_i2c", None) and getattr(self.dev._i2c, "last_error", 0) != 0:
                status_bits |= BUS_ERR
        except Exception:
            pass

        try:
            ax, ay, az = self.dev.accel
            gx, gy, gz = self.dev.gyro
            mx, my, mz = self.dev.magnetic
            roll, pitch, yaw = self.dev.euler
            qw, qx, qy, qz = self.dev.quat
            lx, ly, lz = self.dev.linear
            gxv, gyv, gzv = self.dev.gravity
        except Exception:
            self._stats["last_err"] = BUS_ERR
            raise

        self._emit(Sample(Q_ACC, U_MS2, F_SENSOR, (3,), (ax, ay, az), status_bits, src_str))
        self._emit(Sample(Q_GYRO, U_RAD_S, F_SENSOR, (3,), (gx, gy, gz), status_bits, src_str))
        self._emit(Sample(Q_MAG, U_UT, F_SENSOR, (3,), (mx, my, mz), status_bits, src_str))
        self._emit(Sample(Q_EULER, U_RAD, F_ENU, (3,), (roll, pitch, yaw), status_bits, src_str))
        self._emit(Sample(Q_QUAT, U_NONE, F_ENU, (4,), (qw, qx, qy, qz), status_bits, src_str))
        self._emit(Sample(Q_LINACC, U_MS2, F_SENSOR, (3,), (lx, ly, lz), status_bits, src_str))
        self._emit(Sample(Q_GRAV, U_MS2, F_SENSOR, (3,), (gxv, gyv, gzv),status_bits, src_str))
        return True
