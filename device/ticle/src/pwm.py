import machine
import micropython
import utime

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class Pwm:
    __FULL_RANGE     = 65_535
    __MICROS_PER_SEC = 1_000_000

    def __init__(self, pins: list[int]|tuple[int, ...]):
        if not pins:
            raise ValueError("At least one pin must be provided")
        
        self._pins = list(pins)
        n = len(self._pins)
        
        try:
            self._pwm = [machine.PWM(machine.Pin(pin)) for pin in self._pins]
        except Exception as e:
            raise OSError(f"Failed to initialize PWM pins: {e}")
        
        self._freq_hz = [1000] * n
        self._duty_pct = [0] * n
        self._enabled = [True] * n
        
        for i in range(n):
            self._pwm[i].freq(self._freq_hz[i])
            self._pwm[i].duty_u16(0)

    def deinit(self) -> None:
        try:
            for pwm in self._pwm:
                pwm.duty_u16(0)
            
            utime.sleep_ms(50)
            
            for pwm in self._pwm:
                pwm.deinit()
        except:
            pass

    def __getitem__(self, idx: int|slice) -> "_PwmView":
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(len(self._pins))))
            return Pwm._PwmView(self, indices)
        elif isinstance(idx, int):
            if not (0 <= idx < len(self._pins)):
                raise IndexError("PWM channel index out of range")
            return Pwm._PwmView(self, [idx])
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        return len(self._pins)

    @staticmethod
    def _get_freq_list(parent, indices: list[int]) -> list[int]:
        return [parent._freq_hz[i] for i in indices]

    @staticmethod
    def _set_freq_all(parent, freq: int, indices: list[int]) -> None:
        for i in indices:
            parent._freq_hz[i] = freq
            parent._pwm[i].freq(freq)

    @staticmethod
    @micropython.native
    def _get_period_list(parent, indices: list[int]) -> list[int]:
        return [Pwm.__MICROS_PER_SEC // parent._freq_hz[i] for i in indices]

    @staticmethod
    def _set_period_all(parent, period_us: int, indices: list[int]) -> None:
        freq = Pwm.__MICROS_PER_SEC // period_us
        for i in indices:
            parent._freq_hz[i] = freq
            parent._pwm[i].freq(freq)

    @staticmethod
    def _get_duty_list(parent, indices: list[int]) -> list[int]:
        return [parent._duty_pct[i] for i in indices]

    @staticmethod
    def _set_duty_all(parent, duty_pct: int, indices: list[int]) -> None:
        for i in indices:
            parent._duty_pct[i] = duty_pct
            if parent._enabled[i]:
                raw_duty = int(duty_pct * Pwm.__FULL_RANGE / 100)
                parent._pwm[i].duty_u16(raw_duty)
            else:
                parent._pwm[i].duty_u16(0)

    @staticmethod
    def _get_duty_u16_list(parent, indices: list[int]) -> list[int]:
        return [parent._pwm[i].duty_u16() for i in indices]

    @staticmethod
    def _set_duty_u16_all(parent, duty_raw: int, indices: list[int]) -> None:
        duty_pct = round(duty_raw * 100 / Pwm.__FULL_RANGE)
        for i in indices:
            parent._duty_pct[i] = duty_pct
            if parent._enabled[i]:
                parent._pwm[i].duty_u16(duty_raw)
            else:
                parent._pwm[i].duty_u16(0)

    @staticmethod
    def _get_duty_us_list(parent, indices: list[int]) -> list[int]:
        result = []
        for i in indices:
            period_us = Pwm.__MICROS_PER_SEC // parent._freq_hz[i]
            duty_us = int(parent._duty_pct[i] * period_us / 100)
            result.append(duty_us)
        return result

    @staticmethod
    @micropython.native
    def _set_duty_us_all(parent, duty_us: int, indices: list[int]) -> None:
        for i in indices:
            period_us = Pwm.__MICROS_PER_SEC // parent._freq_hz[i]
            duty_pct = int(duty_us * 100 / period_us)
            duty_pct = max(0, min(100, duty_pct))
            parent._duty_pct[i] = duty_pct
            
            if parent._enabled[i]:
                duty_raw = int(duty_us * Pwm.__FULL_RANGE / period_us)
                duty_raw = max(0, min(Pwm.__FULL_RANGE, duty_raw))
                parent._pwm[i].duty_u16(duty_raw)
            else:
                parent._pwm[i].duty_u16(0)

    @staticmethod
    def _get_enabled_list(parent, indices: list[int]) -> list[bool]:
        return [parent._enabled[i] for i in indices]

    @staticmethod
    def _set_enabled_all(parent, enabled: bool, indices: list[int]) -> None:
        for i in indices:
            parent._enabled[i] = enabled
            if enabled:
                raw_duty = int(parent._duty_pct[i] * Pwm.__FULL_RANGE / 100)
                parent._pwm[i].duty_u16(raw_duty)
            else:
                parent._pwm[i].duty_u16(0)

    class _PwmView:
        def __init__(self, parent: "Pwm", indices: list[int]):
            self._parent = parent
            self._indices = indices

        def __getitem__(self, idx: int|slice) -> "Pwm._PwmView":
            if isinstance(idx, slice):
                selected_indices = [self._indices[i] for i in range(*idx.indices(len(self._indices)))]
                return Pwm._PwmView(self._parent, selected_indices)
            else:
                return Pwm._PwmView(self._parent, [self._indices[idx]])

        def __len__(self) -> int:
            return len(self._indices)

        @property
        def freq(self) -> list[int]:
            return Pwm._get_freq_list(self._parent, self._indices)

        @freq.setter
        def freq(self, hz: int | list[int]):
            if isinstance(hz, (list, tuple)):
                if len(hz) != len(self._indices):
                    raise ValueError("List length must match number of channels")
                for i, f in zip(self._indices, hz):
                    Pwm._set_freq_all(self._parent, f, [i])
            else:
                Pwm._set_freq_all(self._parent, hz, self._indices)

        @property
        def period(self) -> list[int]:
            return Pwm._get_period_list(self._parent, self._indices)

        @period.setter
        def period(self, us: int | list[int]):
            if isinstance(us, (list, tuple)):
                if len(us) != len(self._indices):
                    raise ValueError("List length must match number of channels")
                for i, p in zip(self._indices, us):
                    Pwm._set_period_all(self._parent, p, [i])
            else:
                Pwm._set_period_all(self._parent, us, self._indices)

        @property
        def duty(self) -> list[int]:
            return Pwm._get_duty_list(self._parent, self._indices)

        @duty.setter
        def duty(self, pct: int | list[int]):
            if isinstance(pct, (list, tuple)):
                if len(pct) != len(self._indices):
                    raise ValueError("List length must match number of channels")
                for i, p in zip(self._indices, pct):
                    Pwm._set_duty_all(self._parent, p, [i])
            else:
                Pwm._set_duty_all(self._parent, pct, self._indices)

        @property
        def duty_u16(self) -> list[int]:
            return Pwm._get_duty_u16_list(self._parent, self._indices)

        @duty_u16.setter
        def duty_u16(self, raw: int | list[int]):
            if isinstance(raw, (list, tuple)):
                if len(raw) != len(self._indices):
                    raise ValueError("List length must match number of channels")
                for i, r in zip(self._indices, raw):
                    Pwm._set_duty_u16_all(self._parent, r, [i])
            else:
                Pwm._set_duty_u16_all(self._parent, raw, self._indices)

        @property
        def duty_us(self) -> list[int]:
            return Pwm._get_duty_us_list(self._parent, self._indices)

        @duty_us.setter
        def duty_us(self, us: int | list[int]):
            if isinstance(us, (list, tuple)):
                if len(us) != len(self._indices):
                    raise ValueError("List length must match number of channels")
                for i, u in zip(self._indices, us):
                    Pwm._set_duty_us_all(self._parent, u, [i])
            else:
                Pwm._set_duty_us_all(self._parent, us, self._indices)

        @property
        def enabled(self) -> list[bool]:
            return Pwm._get_enabled_list(self._parent, self._indices)

        @enabled.setter
        def enabled(self, flag: bool | list[bool]):
            if isinstance(flag, (list, tuple)):
                if len(flag) != len(self._indices):
                    raise ValueError("List length must match number of channels")
                for i, en in zip(self._indices, flag):
                    Pwm._set_enabled_all(self._parent, en, [i])
            else:
                Pwm._set_enabled_all(self._parent, flag, self._indices)
