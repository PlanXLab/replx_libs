import machine
import micropython

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class Adc:
    def __init__(self, pins: list[int]|tuple[int, ...]):
        if not pins:
            raise ValueError("At least one pin must be provided")
        
        valid_pins = {26, 27, 28}
        invalid_pins = set(pins) - valid_pins
        if invalid_pins:
            raise ValueError(f"Invalid ADC pins: {invalid_pins}. Only GPIO 26, 27, 28 support ADC on RP2350.")
        
        self._pins = list(pins)
        n = len(self._pins)
        
        try:
            self._adc = [machine.ADC(machine.Pin(pin)) for pin in self._pins]
        except Exception as e:
            raise OSError(f"Failed to initialize ADC pins: {e}")
        
        self._user_callbacks = [None] * n
        self._period_ms = [20] * n
        self._measurement_enabled = [False] * n
        self._timers = [None] * n

    def deinit(self) -> None:
        try:
            for i in range(len(self._pins)):
                self._measurement_enabled[i] = False
                if self._timers[i] is not None:
                    try:
                        self._timers[i].deinit()
                        self._timers[i] = None
                    except:
                        pass
        except:
            pass

    def __getitem__(self, idx: int|slice) -> "_AdcView":
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(len(self._pins))))
            return Adc._AdcView(self, indices)
        elif isinstance(idx, int):
            if not (0 <= idx < len(self._pins)):
                raise IndexError("ADC channel index out of range")
            return Adc._AdcView(self, [idx])
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        return len(self._pins)

    def _setup_timer(self, idx: int) -> None:
        if (self._user_callbacks[idx] is not None and 
            self._period_ms[idx] > 0 and 
            self._measurement_enabled[idx]):
            
            if self._timers[idx] is None:
                def timer_callback(timer):
                    pin_num = self._pins[idx]
                    raw = self._adc[idx].read_u16()
                    voltage = round(raw * (3.3 / 65535), 3)
                    
                    try:
                        micropython.schedule(lambda _: self._user_callbacks[idx](pin_num, voltage, raw), 0)
                    except RuntimeError:
                        try:
                            self._user_callbacks[idx](pin_num, voltage, raw)
                        except:
                            pass
                
                self._timers[idx] = machine.Timer()
                self._timers[idx].init(mode=machine.Timer.PERIODIC, period=self._period_ms[idx], callback=timer_callback)
        else:
            if self._timers[idx] is not None:
                self._timers[idx].deinit()
                self._timers[idx] = None
            
    @staticmethod
    @micropython.native
    def _get_value_list(parent, indices: list[int]) -> list[float]:
        result = []
        for i in indices:
            raw = parent._adc[i].read_u16()
            voltage = raw * (3.3 / 65535)
            result.append(round(voltage, 3))
        return result

    @staticmethod
    def _get_raw_value_list(parent, indices: list[int]) -> list[int]:
        return [parent._adc[i].read_u16() for i in indices]

    @staticmethod
    def _get_callback_list(parent, indices: list[int]) -> list[callable]:
        return [parent._user_callbacks[i] for i in indices]

    @staticmethod
    def _set_callback_all(parent, callback: callable, indices: list[int]) -> None:
        for i in indices:
            parent._user_callbacks[i] = callback
            parent._setup_timer(i)

    @staticmethod
    def _get_period_list(parent, indices: list[int]) -> list[int]:
        return [parent._period_ms[i] for i in indices]

    @staticmethod
    def _set_period_all(parent, period_ms: int, indices: list[int]) -> None:
        for i in indices:
            parent._period_ms[i] = period_ms
            parent._setup_timer(i)

    @staticmethod
    def _get_measurement_list(parent, indices: list[int]) -> list[bool]:
        return [parent._measurement_enabled[i] for i in indices]

    @staticmethod
    def _set_measurement_all(parent, enabled: bool, indices: list[int]) -> None:
        for i in indices:
            parent._measurement_enabled[i] = enabled
            parent._setup_timer(i)

    class _AdcView:
        def __init__(self, parent: "Adc", indices: list[int]):
            self._parent = parent
            self._indices = indices

        def __getitem__(self, idx: int|slice) -> "Adc._AdcView":
            if isinstance(idx, slice):
                selected_indices = [self._indices[i] for i in range(*idx.indices(len(self._indices)))]
                return Adc._AdcView(self._parent, selected_indices)
            else:
                return Adc._AdcView(self._parent, [self._indices[idx]])

        def __len__(self) -> int:
            return len(self._indices)

        @property
        def value(self) -> list[float]:
            return Adc._get_value_list(self._parent, self._indices)

        @property
        def raw_value(self) -> list[int]:
            return Adc._get_raw_value_list(self._parent, self._indices)

        @property
        def callback(self) -> list[callable]:
            return Adc._get_callback_list(self._parent, self._indices)

        @callback.setter
        def callback(self, fn: callable | list[callable]):
            if callable(fn) or fn is None:
                Adc._set_callback_all(self._parent, fn, self._indices)
            else:
                if len(fn) != len(self._indices):
                    raise ValueError("List length must match number of channels")
                for i, callback in zip(self._indices, fn):
                    if not (callable(callback) or callback is None):
                        raise TypeError("Each callback must be callable or None")
                    self._parent._user_callbacks[i] = callback
                    self._parent._setup_timer(i)

        @property
        def period_ms(self) -> list[int]:
            return Adc._get_period_list(self._parent, self._indices)

        @period_ms.setter
        def period_ms(self, ms: int):
            Adc._set_period_all(self._parent, ms, self._indices)

        @property
        def measurement(self) -> list[bool]:
            return Adc._get_measurement_list(self._parent, self._indices)

        @measurement.setter
        def measurement(self, enabled: bool | list[bool]):
            if isinstance(enabled, bool):
                Adc._set_measurement_all(self._parent, enabled, self._indices)
            else:
                if len(enabled) != len(self._indices):
                    raise ValueError("List length must match number of channels")
                for i, en in zip(self._indices, enabled):
                    self._parent._measurement_enabled[i] = en
                    self._parent._setup_timer(i)
