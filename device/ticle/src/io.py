import machine
import micropython
import utime

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


LOW  = micropython.const(0)
HIGH = micropython.const(1)


class Din:
    PULL_DOWN   = machine.Pin.PULL_DOWN
    PULL_UP     = machine.Pin.PULL_UP
    OPEN_DRAIN  = machine.Pin.OPEN_DRAIN
    CB_FALLING  = machine.Pin.IRQ_FALLING
    CB_RISING   = machine.Pin.IRQ_RISING
    CB_BOTH     = machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING
        
    def __init__(self, pins: list[int]|tuple[int, ...]):
        if not pins:
            raise ValueError("At least one pin must be provided")
            
        self._pins = list(pins)
        n = len(self._pins)
        
        try:
            self._din = [machine.Pin(pin, machine.Pin.IN) for pin in self._pins]
        except Exception as e:
            raise OSError(f"Failed to initialize GPIO pins: {e}")
        
        self._pull_config = [None] * n 
        
        self._user_callbacks = [None] * n
        self._edge_config = [0] * n
        self._measurement_enabled = [False] * n
        self._irq_handlers = [None] * n
        self._debounce_us = [0] * n 
        
    def deinit(self) -> None:
        try:
            for i in range(len(self._pins)):
                self._measurement_enabled[i] = False
                if self._irq_handlers[i] is not None:
                    try:
                        self._din[i].irq(handler=None)
                        self._irq_handlers[i] = None
                    except:
                        pass
        except:
            pass

    def __getitem__(self, idx: int|slice) -> "_DinView":
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(len(self._pins))))
            return Din._DinView(self, indices)
        elif isinstance(idx, int):
            if not (0 <= idx < len(self._pins)):
                raise IndexError("Pin index out of range")
            return Din._DinView(self, [idx])
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        return len(self._pins)

    @property
    def pins(self) -> list:
        return self._din

    def _setup_irq(self, idx: int) -> None:
        if (self._user_callbacks[idx] is not None and self._edge_config[idx] != 0 and self._measurement_enabled[idx]):
            
            if self._irq_handlers[idx] is None:
                def irq_handler(pin_obj):
                    pin_num = self._pins[idx]
                    current_value = pin_obj.value()
                    rising = bool(current_value)
                    
                    try:
                        micropython.schedule(
                            lambda _: self._user_callbacks[idx](pin_num, rising), 0
                        )
                    except RuntimeError:
                        try:
                            self._user_callbacks[idx](pin_num, rising)
                        except:
                            pass
                
                self._irq_handlers[idx] = irq_handler
                self._din[idx].irq(trigger=self._edge_config[idx], handler=irq_handler)
        else:
            if self._irq_handlers[idx] is not None:
                self._din[idx].irq(handler=None)
                self._irq_handlers[idx] = None

    @staticmethod
    def _get_pull_list(parent, indices: list[int]) -> list[int|None]:
        return [parent._pull_config[i] for i in indices]

    @staticmethod
    def _set_pull_all(parent, pull: int|None, indices: list[int]) -> None:
        for i in indices:
            parent._pull_config[i] = pull
            parent._din[i].init(mode=machine.Pin.IN, pull=pull)
            
    @staticmethod
    def _get_value_list(parent, indices: list[int]) -> list[int]:
        return [parent._din[i].value() for i in indices]

    @staticmethod
    def _get_callback_list(parent, indices: list[int]) -> list[callable]:
        return [parent._user_callbacks[i] for i in indices]

    @staticmethod
    def _set_callback_all(parent, callback: callable, indices: list[int]) -> None:
        for i in indices:
            parent._user_callbacks[i] = callback
            parent._setup_irq(i)

    @staticmethod
    def _get_edge_list(parent, indices: list[int]) -> list[int]:
        return [parent._edge_config[i] for i in indices]

    @staticmethod
    def _set_edge_all(parent, edge: int, indices: list[int]) -> None:
        for i in indices:
            parent._edge_config[i] = edge
            parent._setup_irq(i)

    @staticmethod
    def _get_measurement_list(parent, indices: list[int]) -> list[bool]:
        return [parent._measurement_enabled[i] for i in indices]

    @staticmethod
    def _set_measurement_all(parent, enabled: bool, indices: list[int]) -> None:
        for i in indices:
            parent._measurement_enabled[i] = enabled
            parent._setup_irq(i)

    @staticmethod
    def _get_debounce_list(parent, indices: list[int]) -> list[int]:
        return [parent._debounce_us[i] for i in indices]

    @staticmethod
    def _set_debounce_all(parent, debounce_us: int, indices: list[int]) -> None:
        for i in indices:
            parent._debounce_us[i] = debounce_us

    class _DinView:
        def __init__(self, parent: "Din", indices: list[int]):
            self._parent = parent
            self._indices = indices

        def __getitem__(self, idx: int|slice) -> "Din._DinView":
            if isinstance(idx, slice):
                selected_indices = [self._indices[i] for i in range(*idx.indices(len(self._indices)))]
                return Din._DinView(self._parent, selected_indices)
            else:
                return Din._DinView(self._parent, [self._indices[idx]])

        def __len__(self) -> int:
            return len(self._indices)

        @property
        def pull(self) -> list[int|None]:
            return Din._get_pull_list(self._parent, self._indices)

        @pull.setter
        def pull(self, pull_type: int|None|list[int|None]):
            if isinstance(pull_type, (list, tuple)):
                if len(pull_type) != len(self._indices):
                    raise ValueError("List length must match number of pins")
                for i, pull in zip(self._indices, pull_type):
                    Din._set_pull_all(self._parent, pull, [i])
            else:
                Din._set_pull_all(self._parent, pull_type, self._indices)
      
        @property
        def value(self) -> list[int]:
            return Din._get_value_list(self._parent, self._indices)

        @property
        def callback(self) -> list[callable]:
            return Din._get_callback_list(self._parent, self._indices)

        @callback.setter
        def callback(self, fn: callable | list[callable]):
            if callable(fn) or fn is None:
                Din._set_callback_all(self._parent, fn, self._indices)
            else:
                if len(fn) != len(self._indices):
                    raise ValueError("List length must match number of pins")
                for i, callback in zip(self._indices, fn):
                    if not (callable(callback) or callback is None):
                        raise TypeError("Each callback must be callable or None")
                    self._parent._user_callbacks[i] = callback
                    self._parent._setup_irq(i)

        @property
        def edge(self) -> list[int]:
            return Din._get_edge_list(self._parent, self._indices)

        @edge.setter
        def edge(self, edge_type: int):
            Din._set_edge_all(self._parent, edge_type, self._indices)

        @property
        def debounce_us(self) -> list[int]:
            return Din._get_debounce_list(self._parent, self._indices)

        @debounce_us.setter
        def debounce_us(self, us: int):
            Din._set_debounce_all(self._parent, us, self._indices)

        @property
        def measurement(self) -> list[bool]:
            return Din._get_measurement_list(self._parent, self._indices)

        @measurement.setter
        def measurement(self, enabled: bool | list[bool]):
            if isinstance(enabled, bool):
                Din._set_measurement_all(self._parent, enabled, self._indices)
            else:
                if len(enabled) != len(self._indices):
                    raise ValueError("List length must match number of pins")
                for i, en in zip(self._indices, enabled):
                    self._parent._measurement_enabled[i] = en
                    self._parent._setup_irq(i)

        def measure_pulse_width(self, level: int, timeout_ms: int = 1000) -> int:
            if len(self._indices) != 1:
                raise ValueError("Pulse width measurement only works with single pin. Use individual pin access like din[0].measure_pulse_width() instead of din[:].measure_pulse_width()")
            
            pin = self._parent._din[self._indices[0]]
            
            return machine.time_pulse_us(pin, level, timeout_ms * 1000)            


class Dout:
    LOGIC_HIGH  = True
    LOGIC_LOW   = False
    PULL_DOWN   = machine.Pin.PULL_DOWN
    PULL_UP     = machine.Pin.PULL_UP
    OPEN_DRAIN  = machine.Pin.OPEN_DRAIN

    def __init__(self, pins: list[int]|tuple[int, ...]):
        if not pins:
            raise ValueError("At least one pin must be provided")
        
        self._pins = list(pins)
        n = len(self._pins)
        
        try:
            self._dout = [machine.Pin(pin, machine.Pin.IN) for pin in self._pins]
        except Exception as e:
            raise OSError(f"Failed to initialize GPIO pins: {e}")
        
        self._pull_config = [None] * n
        self._active_logic = [None] * n 

    def deinit(self) -> None:
        try:
            for i, pin in enumerate(self._dout):
                if self._active_logic[i] == Dout.LOGIC_HIGH:
                    pin.value(0)
                else:
                    pin.value(1)
            
            utime.sleep_ms(50)
            
            for pin in self._dout:
                pin.init(mode=machine.Pin.IN, pull=machine.Pin.PULL_DOWN)
        except:
            pass

    def __getitem__(self, idx: int|slice) -> "_DoutView":
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(len(self._pins))))
            return Dout._DoutView(self, indices)
        elif isinstance(idx, int):
            if not (0 <= idx < len(self._pins)):
                raise IndexError("Pin index out of range")
            return Dout._DoutView(self, [idx])
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        return len(self._pins)

    @property
    def pins(self) -> list:
        return self._dout

    @staticmethod
    def _get_pull_list(parent, indices: list[int]) -> list[int|None]:
        return [parent._pull_config[i] for i in indices]

    @staticmethod
    def _set_pull_all(parent, pull: int|None, indices: list[int]) -> None:
        for i in indices:
            parent._pull_config[i] = pull
            parent._dout[i].init(mode=machine.Pin.OUT, pull=pull)

    @staticmethod
    def _get_active_list(parent, indices: list[int]) -> list[bool]:
        return [parent._active_logic[i] for i in indices]

    @staticmethod
    def _set_active_all(parent, active_logic: bool, indices: list[int]) -> None:
        for i in indices:
            if parent._active_logic[i] is None:
                parent._dout[i].init(mode=machine.Pin.OUT)
                parent._active_logic[i] = active_logic
                 
                if active_logic == Dout.LOGIC_HIGH:
                    parent._dout[i].value(0)
                else:
                    parent._dout[i].value(1)
            else:
                parent._active_logic[i] = active_logic

    @staticmethod
    def _get_value_list(parent, indices: list[int]) -> list[int]:
        result = []
        for i in indices:
            physical = parent._dout[i].value()
            if parent._active_logic[i] == Dout.LOGIC_HIGH:
                logical = physical
            else:
                logical = 1 - physical
            result.append(logical)
        return result

    @staticmethod
    def _set_value_all(parent, logical_value: int, indices: list[int]) -> None:
        for i in indices:
            if parent._active_logic[i] == Dout.LOGIC_HIGH:
                physical_value = logical_value
            else:
                physical_value = 1 - logical_value
            parent._dout[i].value(physical_value)

    @staticmethod
    def _set_value_list(parent, logical_values: list[int], indices: list[int]) -> None:
        if len(logical_values) != len(indices):
            raise ValueError(f"Value list length ({len(logical_values)}) must match pin count ({len(indices)})")
        for i, logical_value in zip(indices, logical_values):
            if parent._active_logic[i] == Dout.LOGIC_HIGH:
                physical_value = logical_value
            else:
                physical_value = 1 - logical_value
            parent._dout[i].value(physical_value)

    @staticmethod
    def _toggle_all(parent, indices: list[int]) -> None:
        for i in indices:
            physical = parent._dout[i].value()
            if parent._active_logic[i] == Dout.LOGIC_HIGH:
                logical = physical
            else:
                logical = 1 - physical
            
            new_logical = 1 - logical
            
            if parent._active_logic[i] == Dout.LOGIC_HIGH:
                new_physical = new_logical
            else:
                new_physical = 1 - new_logical
            
            parent._dout[i].value(new_physical)

    class _DoutView:
        def __init__(self, parent: "Dout", indices: list[int]):
            self._parent = parent
            self._indices = indices

        def __getitem__(self, idx: int|slice) -> "Dout._DoutView":
            if isinstance(idx, slice):
                selected_indices = [self._indices[i] for i in range(*idx.indices(len(self._indices)))]
                return Dout._DoutView(self._parent, selected_indices)
            else:
                return Dout._DoutView(self._parent, [self._indices[idx]])

        def __len__(self) -> int:
            return len(self._indices)

        @property
        def active(self) -> list[bool]:
            return Dout._get_active_list(self._parent, self._indices)

        @active.setter
        def active(self, logic_type: bool | list[bool]):
            if isinstance(logic_type, (list, tuple)):
                if len(logic_type) != len(self._indices):
                    raise ValueError("List length must match number of pins")
                for i, logic in zip(self._indices, logic_type):
                    Dout._set_active_all(self._parent, logic, [i])
            else:
                Dout._set_active_all(self._parent, logic_type, self._indices)

        @property
        def pull(self) -> list[int|None]:
            return Dout._get_pull_list(self._parent, self._indices)

        @pull.setter
        def pull(self, pull_type: int|None|list[int|None]):
            if isinstance(pull_type, (list, tuple)):
                if len(pull_type) != len(self._indices):
                    raise ValueError("List length must match number of pins")
                for i, pull in zip(self._indices, pull_type):
                    Dout._set_pull_all(self._parent, pull, [i])
            else:
                Dout._set_pull_all(self._parent, pull_type, self._indices)

        @property
        def value(self) -> list[int]:
            return Dout._get_value_list(self._parent, self._indices)

        @value.setter
        def value(self, val: int | list[int]):
            if isinstance(val, (list, tuple)):
                Dout._set_value_list(self._parent, val, self._indices)
            else:
                Dout._set_value_all(self._parent, val, self._indices)

        def toggle(self) -> None:
            Dout._toggle_all(self._parent, self._indices)

        @property
        def physical_value(self) -> list[int]:
            return [self._parent._dout[i].value() for i in self._indices]
