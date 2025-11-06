__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"

from array import array
from math import exp, pi, sqrt, tan, fabs
import micropython


class FilterError(Exception):
    """Base exception for filter-related errors"""
    pass

class FilterConfigurationError(FilterError):
    """Raised when filter parameters are invalid"""
    pass

class FilterOperationError(FilterError):
    """Raised when filter operation fails"""
    pass


class Base:
    def __init__(self) -> None:
        self._sample_count = 0

    def update(self, x: float) -> float:
        raise NotImplementedError("Subclasses must implement update method")
    
    def reset(self) -> None:
        self._sample_count = 0
    
    def __call__(self, x: float) -> float:
        return self.update(x)
    
    def process_batch(self, samples: list) -> list:
        if not hasattr(samples, '__iter__'):
            raise TypeError("samples must be iterable")
        
        return [self.update(sample) for sample in samples]
    
    @property
    def sample_count(self) -> int:
        return self._sample_count
    
    def _validate_numeric(self, value: float, name: str, min_val: float = None, max_val: float = None) -> float:
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise FilterConfigurationError(f"{name} must be a number, got {type(value).__name__}")

        if min_val is not None and value < min_val:
            raise FilterConfigurationError(f"{name} must be >= {min_val}, got {value}")

        if max_val is not None and value > max_val:
            raise FilterConfigurationError(f"{name} must be <= {max_val}, got {value}")

        return value


class Alpha(Base):
    def __init__(self, alpha: float, initial: float = 0.0) -> None:
        super().__init__()
        if alpha <= 0.0 or alpha > 1.0:
            raise FilterConfigurationError("alpha must be in range (0, 1]")
        self._alpha = float(alpha)
        self.y = float(initial)
        self._initial_value = float(initial)

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, value: float) -> None:
        if value <= 0.0 or value > 1.0:
            raise FilterConfigurationError("alpha must be in range (0, 1]")
        self._alpha = float(value)

    @micropython.native
    def update(self, x: float) -> float:
        self._sample_count += 1
        x = float(x)
        self.y = self._alpha * x + (1.0 - self._alpha) * self.y
        return self.y
    
    def reset(self) -> None:
        super().reset()
        self.y = self._initial_value


class LowPass(Base):
    def __init__(self, fc: float, fs: float, initial: float = 0.0) -> None:
        super().__init__()  
        if fs <= 0:
            raise FilterConfigurationError("Sampling frequency must be positive")
        
        # Validate cutoff frequency and Nyquist criterion
        if fc <= 0 or fc >= fs / 2:
            raise FilterConfigurationError("Cutoff frequency must be between 0 and {}".format(fs/2))
        
        self.fs = float(fs)
        self.fc = float(fc)
        
        # Calculate filter coefficient using bilinear transform equivalent
        self._alpha = 1.0 - exp(-2.0 * pi * fc / fs)
        
        self.y = float(initial)
        self._initial_value = float(initial)

    @micropython.native
    def update(self, x: float) -> float:
        self._sample_count += 1
        x = float(x)
        self.y = self._alpha * x + (1.0 - self._alpha) * self.y
        return self.y
    
    def reset(self) -> None:
        super().reset()
        self.y = self._initial_value


class HighPass(Base):    
    def __init__(self, fc: float, fs: float, initial: float = 0.0) -> None:
        super().__init__()
        if fs <= 0:
            raise FilterConfigurationError("Sampling frequency must be positive")
        if fc <= 0 or fc >= fs / 2:
            raise FilterConfigurationError("Cutoff frequency must be between 0 and {}".format(fs/2))
        
        self.fs = float(fs)
        self.fc = float(fc)
        self.a = exp(-2.0 * pi * fc / fs)
        self.y = float(initial)
        self.x_prev = float(initial)
        self._initial_value = float(initial)

    @micropython.native
    def update(self, x: float) -> float:
        self._sample_count += 1
        x = float(x)
        self.y = self.a * (self.y + x - self.x_prev)
        self.x_prev = x
        return self.y
    
    def reset(self) -> None:
        super().reset()
        self.y = self._initial_value
        self.x_prev = self._initial_value


class TauLowPass(Base):
    def __init__(self, tau_s: float, initial: float = 0.0, fs: float = None) -> None:
        super().__init__()
        if tau_s <= 0.0:
            raise ValueError("tau_s must be > 0")
        self._tau = float(tau_s)

        self.y = float(initial)
        self._initial_value = float(initial)

        if fs is not None:
            if fs <= 0.0:
                raise ValueError("fs must be > 0 when provided")
            self.fs = float(fs)
            self._alpha_fixed = self._compute_alpha_fixed()
        else:
            self.fs = None
            self._alpha_fixed = None

    @property
    def tau(self) -> float:
        return self._tau

    @tau.setter
    def tau(self, value: float) -> None:
        if value <= 0.0:
            raise ValueError("tau must be > 0")
        self._tau = float(value)
        if self.fs is not None:
            self._alpha_fixed = self._compute_alpha_fixed()

    def set_cutoff(self, fc_hz: float) -> None:
        if fc_hz <= 0.0:
            raise ValueError("fc must be > 0")
        self.tau = 1.0 / (2.0 * pi * float(fc_hz))

    def _compute_alpha_fixed(self) -> float:
        return 1.0 - exp(-(1.0 / self.fs) / self._tau)

    @micropython.native
    def update_with_dt(self, x: float, dt_s: float) -> float:
        self._sample_count += 1
        x_val = float(x)
        dt = float(dt_s)

        if dt <= 0.0 or dt < 1e-9:
            return self.y

        a = 1.0 - exp(-dt / self._tau)
        if a < 0.0:
            a = 0.0
        elif a > 1.0:
            a = 1.0

        self.y = a * x_val + (1.0 - a) * self.y
        return self.y

    @micropython.native
    def update(self, x: float) -> float:
        if self._alpha_fixed is None:
            raise FilterOperationError(
                "TauLowPass.update() requires fixed fs. "
                "Use update_with_dt(x, dt) or pass fs in the constructor."
            )

        self._sample_count += 1
        x_val = float(x)
        a = self._alpha_fixed
        self.y = a * x_val + (1.0 - a) * self.y
        return self.y

    def reset(self) -> None:
        super().reset()
        self.y = self._initial_value


class SlewRateLimiter(Base):    
    def __init__(self, rise_per_s: float, fall_per_s: float = None, initial: float = 0.0, fs: float = None, deadband: float = 0.0) -> None:
        super().__init__()

        if rise_per_s is None or rise_per_s <= 0.0:
            raise ValueError("rise_per_s must be > 0")
        if fall_per_s is None:
            fall_per_s = rise_per_s
        if fall_per_s <= 0.0:
            raise ValueError("fall_per_s must be > 0")
        if deadband < 0.0:
            raise ValueError("deadband must be >= 0")

        self._rise = float(rise_per_s)
        self._fall = float(fall_per_s)
        self._deadband = float(deadband)

        self.y = float(initial)
        self._initial_value = float(initial)

        if fs is not None:
            if fs <= 0.0:
                raise ValueError("fs must be > 0 when provided")
            self.fs = float(fs)
            self._step_up = self._rise / self.fs
            self._step_down = self._fall / self.fs
        else:
            self.fs = None
            self._step_up = None
            self._step_down = None

    @property
    def rise_per_s(self) -> float:
        return self._rise

    @rise_per_s.setter
    def rise_per_s(self, value: float) -> None:
        if value <= 0.0:
            raise ValueError("rise_per_s must be > 0")
        self._rise = float(value)
        if self.fs is not None:
            self._step_up = self._rise / self.fs

    @property
    def fall_per_s(self) -> float:
        return self._fall

    @fall_per_s.setter
    def fall_per_s(self, value: float) -> None:
        if value <= 0.0:
            raise ValueError("fall_per_s must be > 0")
        self._fall = float(value)
        if self.fs is not None:
            self._step_down = self._fall / self.fs

    @property
    def deadband(self) -> float:
        return self._deadband

    @deadband.setter
    def deadband(self, value: float) -> None:
        if value < 0.0:
            raise ValueError("deadband must be >= 0")
        self._deadband = float(value)

    def set_fs(self, fs: float) -> None:
        if fs <= 0.0:
            raise ValueError("fs must be > 0")
        self.fs = float(fs)
        self._step_up = self._rise / self.fs
        self._step_down = self._fall / self.fs

    @micropython.native
    def update_with_dt(self, x: float, dt_s: float) -> float:
        self._sample_count += 1
        x_val = float(x)
        dt = float(dt_s)

        if dt <= 0.0:
            return self.y

        delta = x_val - self.y
        if fabs(delta) <= self._deadband:
            return self.y

        max_up = self._rise * dt
        max_dn = self._fall * dt

        if delta > 0.0:
            step = delta if delta <= max_up else max_up
        else:
            step = delta if delta >= -max_dn else -max_dn

        self.y += step
        return self.y

    @micropython.native
    def update(self, x: float) -> float:
        if self._step_up is None or self._step_down is None:
            raise FilterOperationError(
                "SlewRateLimiter.update() requires fixed fs. "
                "Use update_with_dt(x, dt) or call set_fs(fs)."
            )

        self._sample_count += 1
        x_val = float(x)

        delta = x_val - self.y
        if fabs(delta) <= self._deadband:
            return self.y

        if delta > 0.0:
            step = delta if delta <= self._step_up else self._step_up
        else:
            step = delta if delta >= -self._step_down else -self._step_down

        self.y += step
        return self.y

    def reset(self) -> None:
        super().reset()
        self.y = self._initial_value


class MovingAverage(Base):
    def __init__(self, window_size: int, initial: float = 0.0) -> None:
        super().__init__()
        
        if not isinstance(window_size, int) or window_size <= 0:
            raise FilterConfigurationError("window_size must be a positive integer")
        
        self._window_size = window_size
        self._initial_value = float(initial)
        self._buf = array("f", [self._initial_value] * self._window_size)
        self._sum = float(self._initial_value * self._window_size)
        self._idx = 0
        self._count = 0

    @micropython.native
    def update(self, x: float) -> float:
        x_val = float(x)
        idx = int(self._idx)
        count = int(self._count)
        window_size = int(self._window_size)
        
        old_value = float(self._buf[idx])
        
        self._sum += x_val - old_value
        self._buf[idx] = x_val
        
        self._idx = (idx + 1) % window_size
        if count < window_size:
            count += 1
            self._count = count

        self._sample_count += 1
        
        return float(self._sum / count)

    def reset(self) -> None:
        super().reset()
        for i in range(self._window_size):
            self._buf[i] = self._initial_value
        self._sum = self._initial_value * self._window_size
        self._idx = 0
        self._count = 0


class Median(Base):
    def __init__(self, window_size: int, initial: float = 0.0) -> None:
        super().__init__()
        if not isinstance(window_size, int) or window_size <= 0:
            raise FilterConfigurationError("window_size must be positive int")
        
        self._initial_value = float(initial)
        self._window_size = window_size        
        self.reset()
        self._sorted_idx = 0

    @micropython.native
    def update(self, x: float) -> float:
        self._sample_count += 1
        x = float(x)

        old = float(self._ring[self._idx])
        self._ring[self._idx] = x
        self._idx = (self._idx + 1) % self._window_size
        if self._count < self._window_size:
            self._sorted[self._count] = x
            self._count += 1
            i = self._count - 1
            while i > 0 and self._sorted[i-1] > self._sorted[i]:
                self._sorted[i-1], self._sorted[i] = self._sorted[i], self._sorted[i-1]
                i -= 1
        else:
            i = int(self._sorted_idx)
            n = self._window_size
            while i > 0 and self._sorted[i] != old and self._sorted[i-1] >= old:
                 i -= 1
            
            while i < n and self._sorted[i] != old:
                i += 1
                
            if i < n:
                while i < n-1:
                    self._sorted[i] = self._sorted[i+1]
                    i += 1

            j = n - 1
            while j > 0 and self._sorted[j-1] > x:
                self._sorted[j] = self._sorted[j-1]
                j -= 1
                
            self._sorted[j] = x
            self._sorted_idx = j
            
        n = self._count
        mid = n >> 1
        return float(self._sorted[mid]) if n & 1 else 0.5 * (self._sorted[mid-1] + self._sorted[mid])

    def reset(self) -> None:
        super().reset()
        self._ring = array("f", [self._initial_value] * self._window_size)
        self._sorted = [self._initial_value] * self._window_size
        self._idx = 0
        self._count = 0


class RMS(Base):
    def __init__(self, window_size: int) -> None:
        super().__init__()
        
        if not isinstance(window_size, int) or window_size <= 0:
            raise FilterConfigurationError("window_size must be a positive integer")
        
        self._window_size = window_size
        self.reset()

    @micropython.native
    def update(self, x: float) -> float:
        x_val = float(x)
        idx = int(self._idx)
        count = int(self._count)
        window_size = int(self._window_size)
        
        old_value = float(self._buf[idx])
        self._sum_of_squares += x_val * x_val - old_value * old_value
        self._buf[idx] = x_val
        
        self._idx = (idx + 1) % window_size
        if count < window_size:
            count += 1
            self._count = count

        self._sample_count += 1
        
        return sqrt(max(0.0, self._sum_of_squares / count))

    def reset(self) -> None:
        super().reset()
        self._buf = array("f", [0.0] * self._window_size)
        self._sum_of_squares = 0.0
        self._idx = 0
        self._count = 0


class Kalman(Base):
    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1, 
                 initial_estimate: float = 0.0, initial_error: float = 1.0, p_cap: float = 100.0) -> None:
        super().__init__() 
        
        if process_noise < 0:
            raise FilterConfigurationError("Process noise must be non-negative")
        if measurement_noise <= 0:
            raise FilterConfigurationError("Measurement noise must be positive")
        
        self.q = float(process_noise)
        self.r = float(measurement_noise)
        self.x = float(initial_estimate)
        self.p = float(initial_error)
        self._initial_estimate = float(initial_estimate)
        self._initial_error = float(initial_error)
        self._p_cap = float(p_cap)
        
    @micropython.native
    def update(self, measurement: float) -> float:
        z = float(measurement)
        
        p_pred = float(self.p + self.q)
        
        if p_pred > self._p_cap:
            self.p = 1.0
            p_pred = 1.0 + float(self.q)  # reset + small inflate
        
        k = p_pred / (p_pred + float(self.r))
        innovation = z - float(self.x)
        
        if fabs(innovation) > 3.0 * sqrt(p_pred):
            k *= 0.1  # Reduce Kalman gain for outliers
        
        self.x = float(self.x) + k * innovation
        self.p = (1.0 - k) * p_pred
        
        self._sample_count += 1
        return float(self.x)

    def reset(self) -> None:
        super().reset()
        self.x = self._initial_estimate
        self.p = self._initial_error


class Adaptive(Base):
    def __init__(self, alpha_min: float = 0.01, alpha_max: float = 0.9, 
                 threshold: float = 0.1, initial: float = 0.0) -> None:
        super().__init__()
        
        if not (0.0 < alpha_min < 1.0):
            raise FilterConfigurationError("alpha_min must be in range (0, 1)")
        if not (0.0 < alpha_max <= 1.0):
            raise FilterConfigurationError("alpha_max must be in range (0, 1]")
        if alpha_min >= alpha_max:
            raise FilterConfigurationError("alpha_min must be < alpha_max")
        if threshold < 0:
            raise FilterConfigurationError("threshold must be non-negative")
        
        self.alpha_min = float(alpha_min)
        self.alpha_max = float(alpha_max)
        self.threshold = float(threshold)
        self.y = float(initial)
        self.prev_x = float(initial)
        self._initial_value = float(initial)

    @micropython.native
    def update(self, x: float) -> float:
        self._sample_count += 1
        x = float(x)
        
        change = fabs(x - self.prev_x)
        
        if change > self.threshold:
            alpha = self.alpha_max  # Fast tracking for large changes
        else:
            ratio = change / self.threshold if self.threshold > 0 else 0
            alpha = self.alpha_min + ratio * (self.alpha_max - self.alpha_min)
        
        self.y = alpha * x + (1.0 - alpha) * self.y
        self.prev_x = x
        
        return self.y

    def reset(self) -> None:
        super().reset()
        self.y = self._initial_value
        self.prev_x = self._initial_value


class Biquad(Base):
    def __init__(self, b0: float, b1: float, b2: float, a1: float, a2: float) -> None:
        super().__init__()
        self.set_coefficients(b0, b1, b2, a1, a2)
        self.reset()

    def set_coefficients(self, b0: float, b1: float, b2: float, a1: float, a2: float) -> None:
        self.b0 = float(b0); self.b1 = float(b1); self.b2 = float(b2)
        self.a1 = float(a1); self.a2 = float(a2)

    @micropython.native
    def update(self, x: float) -> float:
        self._sample_count += 1
        x = float(x)
        # DF-II Transposed states
        w0 = x - self.a1 * self.z1 - self.a2 * self.z2  # a1,a2 are +den coefficients (a0=1)
        y  = self.b0 * w0 + self.b1 * self.z1 + self.b2 * self.z2
        self.z2 = self.z1
        self.z1 = w0
        return y

    def reset(self) -> None:
        super().reset()
        self.z1 = 0.0
        self.z2 = 0.0


class Butterworth(Biquad):
    def __init__(self, fc: float, fs: float, filter_type: str = 'lowpass') -> None:
        if filter_type not in ('lowpass', 'highpass'):
            raise FilterConfigurationError("filter_type must be 'lowpass' or 'highpass'")
        
        if fs <= 0:
            raise FilterConfigurationError("Sampling frequency must be positive")
        if fc <= 0 or fc >= fs / 2:
            raise FilterConfigurationError("Cutoff frequency must be between 0 and {}".format(fs/2))
        
        self.fc = float(fc)
        self.fs = float(fs)
        self.filter_type = filter_type
        
        coeffs = self._design_filter(fc, fs, filter_type)
        super().__init__(*coeffs)

    def _design_filter(self, fc: float, fs: float, filter_type: str) -> tuple:
        wc = 2.0 * pi * fc / fs
        k = tan(wc / 2.0)
        
        if filter_type == 'lowpass':
            norm = 1.0 / (1.0 + sqrt(2.0) * k + k * k)
            b0 = k * k * norm
            b1 = 2.0 * b0
            b2 = b0
            a1 = 2.0 * (k * k - 1.0) * norm
            a2 = (1.0 - sqrt(2.0) * k + k * k) * norm
        else:  # highpass
            norm = 1.0 / (1.0 + sqrt(2.0) * k + k * k)
            b0 = norm
            b1 = -2.0 * b0
            b2 = b0
            a1 = 2.0 * (k * k - 1.0) * norm
            a2 = (1.0 - sqrt(2.0) * k + k * k) * norm
        
        return (b0, b1, b2, a1, a2)
    
    @micropython.native
    def update(self, x: float) -> float:
        return super().update(x)
    
    def reset(self) -> None:
        super().reset()


class FIR(Base):
    def __init__(self, taps: list) -> None:
        super().__init__()
        self.taps = taps
        self.reset()

    @property
    def taps(self) -> list:
        return list(self._taps)

    @taps.setter
    def taps(self, taps: list) -> None:
        if not taps:
            raise FilterConfigurationError("taps list cannot be empty")
        
        self._taps = array("f", [float(t) for t in taps])
        self.n = len(self._taps)
        if hasattr(self, '_buf'):
            self._buf = array("f", [0.0] * self.n)
            self._idx = 0

    @micropython.native
    def update(self, x: float) -> float:
        self._sample_count += 1
        x = float(x)
        
        self._buf[self._idx] = x
        
        acc = 0.0
        tap_i = 0
        buf_i = self._idx
        n = self.n
        b = self._buf; t = self._taps
        while tap_i < n:
            acc += b[buf_i] * t[tap_i]
            buf_i = buf_i - 1 if buf_i > 0 else n - 1
            tap_i += 1
        
        self._idx = (self._idx + 1) % self.n
        return acc

    def reset(self) -> None:
        super().reset()
        self._buf = array("f", [0.0] * self.n)
        self._idx = 0


class AngleEMA(Base):
    _TAU = 2.0 * pi

    def __init__(self, alpha=0.25, initial=None):
        super().__init__()
        self._alpha = self._validate_numeric(alpha, "alpha", 1e-9, 1.0)
        self._rad   = 0.0
        self._have  = False
        if initial is None:
            self.reset()
        else:
            self.reset(initial)

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, value: float) -> None:
        self._alpha = self._validate_numeric(value, "alpha", 1e-9, 1.0)

    @property
    def value(self) -> float:
        return self._rad

    def reset(self, rad=None) -> None:
        super().reset()
        if rad is None:
            self._have = False
            self._rad  = 0.0
        else:
            self._have = True
            r = float(rad)
            self._rad = ((r + pi) % self._TAU) - pi

    @micropython.native
    def update(self, rad: float) -> float:
        self._sample_count += 1
        r = float(rad)

        if not self._have:
            self._rad  = ((r + pi) % self._TAU) - pi
            self._have = True
            return self._rad

        diff = ((r - self._rad) + pi) % self._TAU - pi
        self._rad = (self._rad + self._alpha * diff + pi) % self._TAU - pi
        return self._rad


class PID(Base):
    AW_NONE = 0
    AW_CLAMP = 1
    AW_BACKCALC = 2

    def __init__(self, kp:float, ki:float, kd:float,
                 *, fs:float=None,
                 out_min:float=-1.0, out_max:float=1.0,
                 i_min:float=None, i_max:float=None,
                 beta:float=1.0,
                 tau_d_filter:float=0.0,
                 aw_mode:int=AW_CLAMP, k_aw:float=1.0):
        super().__init__()
        if kp < 0 or ki < 0 or kd < 0:
            raise FilterConfigurationError("kp, ki, kd must be >= 0")
        self.kp = float(kp); self.ki = float(ki); self.kd = float(kd)

        self.fs = float(fs) if fs and fs > 0 else None
        self.dt_fixed = (1.0/self.fs) if self.fs else None

        if out_min > out_max:
            out_min, out_max = out_max, out_min
        self.out_min = float(out_min); self.out_max = float(out_max)

        if i_min is not None and i_max is not None and i_min > i_max:
            i_min, i_max = i_max, i_min
        self.i_min = float(i_min) if i_min is not None else self.out_min
        self.i_max = float(i_max) if i_max is not None else self.out_max

        self.beta = 1.0 if beta is None else float(beta)
        if self.beta < 0.0: self.beta = 0.0
        if self.beta > 1.0: self.beta = 1.0

        self.tau_d = float(tau_d_filter) if tau_d_filter and tau_d_filter > 0 else 0.0

        self.aw_mode = int(aw_mode)
        self.k_aw = float(k_aw) if k_aw is not None else 1.0
        if self.k_aw < 0.0: self.k_aw = 0.0

        self.setpoint = 0.0
        self._i = 0.0
        self._y_prev = 0.0
        self._d_filt = 0.0
        self._have_prev = False
        self.u = 0.0

        self._tracking_on = False
        self._u_track = 0.0

    def set_output_limits(self, out_min, out_max, clamp_i=True):
        if out_max <= out_min:
            raise FilterConfigurationError("out_max must be > out_min")
        self.out_min, self.out_max = float(out_min), float(out_max)
        self.i_min = max(self.out_min, min(self.i_min, self.out_max))
        self.i_max = max(self.out_min, min(self.i_max, self.out_max))
        if self.i_max < self.i_min:
            self.i_min, self.i_max = self.i_max, self.i_min
        if clamp_i:
            self._i = max(self.i_min, min(self._i, self.i_max))

    def set_gains(self, kp=None, ki=None, kd=None):
        if kp is not None:
            if kp < 0: raise FilterConfigurationError("kp must be >= 0")
            self.kp = float(kp)
        if ki is not None:
            if ki < 0: raise FilterConfigurationError("ki must be >= 0")
            self.ki = float(ki)
        if kd is not None:
            if kd < 0: raise FilterConfigurationError("kd must be >= 0")
            self.kd = float(kd)

    def set_beta(self, beta:float):
        b = float(beta)
        if b < 0.0 or b > 1.0:
            raise FilterConfigurationError("beta in [0,1]")
        self.beta = b

    def set_tau_d(self, tau:float):
        self.tau_d = float(tau) if tau and tau > 0 else 0.0

    def set_aw(self, mode:int=None, k_aw:float=None):
        if mode is not None: self.aw_mode = int(mode)
        if k_aw is not None: self.k_aw = max(0.0, float(k_aw))

    def preload_integrator(self, i0:float):
        self._i = max(self.i_min, min(float(i0), self.i_max))

    def start_tracking(self, u_manual:float):
        self._tracking_on = True
        self._u_track = float(u_manual)

    def stop_tracking(self):
        self._tracking_on = False

    def reset(self):
        super().reset()
        self._i = 0.0
        self._y_prev = 0.0
        self._d_filt = 0.0
        self._have_prev = False
        self.u = 0.0
        self._tracking_on = False

    @micropython.native
    def _step(self, y:float, dt:float) -> float:
        sp = self.setpoint
        if self._tracking_on:
            eP = (self.beta * sp) - y
            if not self._have_prev or dt <= 0.0:
                dy = 0.0
            else:
                dy = (y - self._y_prev) / dt
            if self.tau_d > 0.0 and dt > 0.0:
                a = dt / (self.tau_d + dt)
                self._d_filt = (1.0 - a) * self._d_filt + a * dy
                u_d = - self.kd * self._d_filt
            else:
                u_d = - self.kd * dy

            u_p = self.kp * eP
            self._i = max(self.i_min, min(self._u_track - u_p - u_d, self.i_max))
            self.u = max(self.out_min, min(self._u_track, self.out_max))
            self._y_prev = y
            self._have_prev = True
            self._sample_count += 1
            return self.u

        eP = (self.beta * sp) - y 
        eI = (sp - y)
        if not self._have_prev or dt <= 0.0:
            dy = 0.0
        else:
            dy = (y - self._y_prev) / dt
        if self.tau_d > 0.0 and dt > 0.0:
            a = dt / (self.tau_d + dt)
            self._d_filt = (1.0 - a) * self._d_filt + a * dy
            u_d = - self.kd * self._d_filt
        else:
            u_d = - self.kd * dy

        u_p = self.kp * eP
        u_unsat = u_p + self._i + u_d

        if dt > 0.0:
            if self.aw_mode == self.AW_BACKCALC:
                u_sat = u_unsat
                if u_sat > self.out_max: u_sat = self.out_max
                if u_sat < self.out_min: u_sat = self.out_min
                self._i += self.ki * eI * dt + self.k_aw * (u_sat - u_unsat) * dt
                if self._i > self.i_max: self._i = self.i_max
                if self._i < self.i_min: self._i = self.i_min
            elif self.aw_mode == self.AW_CLAMP:
                i_next = self._i + self.ki * eI * dt
                will_up   = (u_unsat > self.out_max) and (i_next > self._i)
                will_down = (u_unsat < self.out_min) and (i_next < self._i)
                if not (will_up or will_down):
                    self._i = i_next
                    if self._i > self.i_max: self._i = self.i_max
                    if self._i < self.i_min: self._i = self.i_min
            else:
                self._i += self.ki * eI * dt
                if self._i > self.i_max: self._i = self.i_max
                if self._i < self.i_min: self._i = self.i_min

        u_temp = u_p + self._i + u_d
        if u_temp > self.out_max: u_temp = self.out_max
        if u_temp < self.out_min: u_temp = self.out_min

        self.u = u_temp
        self._y_prev = y
        self._have_prev = True
        self._sample_count += 1
        return self.u

    def update(self, meas:float, dt_s: float|None = None) -> float:
        if self.dt_fixed is None and dt_s is None:
            raise FilterOperationError("dt_s must be provided when fs is not set")
        return self._step(float(meas), dt_s if dt_s is not None else self.dt_fixed)

    def set_setpoint(self, sp:float, keep_output:bool=False):
        sp = float(sp)
        if keep_output and self._have_prev:
            eP_new = (self.beta * sp) - self._y_prev
            I_new = self.u - self.kp * eP_new
            self._i = max(self.i_min, min(I_new, self.i_max))
        self.setpoint = sp


class FilterChain(Base):    
    def __init__(self, *filters: Base) -> None:
        super().__init__()
        if not filters:
            raise FilterConfigurationError("At least one filter required")
        
        for f in filters:
            if not isinstance(f, Base):
                raise FilterConfigurationError("All items must be Base instances, got {}".format(type(f)))
        
        self.filters = list(filters)

    @micropython.native
    def update(self, x: float) -> float:
        self._sample_count += 1  # Chain-level count (each sub-filter maintains its own)
        result = float(x)
        for filter_obj in self.filters:
            result = filter_obj.update(result)
        return result

    def reset(self) -> None:
        super().reset()
        for filter_obj in self.filters:
            filter_obj.reset()

    def add_filter(self, filter_obj: Base) -> None:
        if not isinstance(filter_obj, Base):
            raise FilterConfigurationError("filter_obj must be Base instance")
        self.filters.append(filter_obj)

    def remove_filter(self, index: int) -> Base:
        if not (0 <= index < len(self.filters)):
            raise FilterConfigurationError("Filter index out of range")
        return self.filters.pop(index)

