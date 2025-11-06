import sys
import gc
import usys
import utime
import uos
import uselect
import ustruct

import machine
import micropython
import network
import bluetooth
import rp2

from ringbuffer import RingBuffer
from termviz import Color


__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


try:
    micropython.alloc_emergency_exception_buf(128)
except Exception:
    pass

@micropython.native
def get_sys_info() -> tuple:
    freq = machine.freq()

    try:
        machine.Pin(43, machine.Pin.IN)
        TEMP_ADC  = 8
    except ValueError: # rp2350a (pico2w)
        TEMP_ADC  = 4
                         
    raw = machine.ADC(TEMP_ADC).read_u16()
    temp = 27 - ((raw * 3.3 / 65535) - 0.706) / 0.001721
    
    return freq, temp


@micropython.native
def get_mem_info() -> tuple:
    gc.collect()
    
    free = gc.mem_free()
    used = gc.mem_alloc()
    total = free + used
    
    return free, used, total

@micropython.native
def get_fs_info(path: str = '/') -> tuple:
    stats = uos.statvfs(path)
    block_size = stats[0]
    total_blocks = stats[2]
    free_blocks = stats[3]

    total = block_size * total_blocks
    free = block_size * free_blocks
    used = total - free
    usage_pct = round(used / total * 100, 2)

    return total, used, free, usage_pct


#------------------------------------------------------------------------------------------------------
# KeyReader class
#------------------------------------------------------------------------------------------------------

class KeyReader():
    ESC = b'\x1b'
    EXT_CODE_TBL = {b'[A': b'UP', b'[B': b'DOWN', b'[C': b'RIGHT', b'[D': b'LEFT', b'\t': b'TAB', b'\r': b'ENTER', b' ': b'SPACE'}
    
    def __enter__(self):
        self.poller = uselect.poll()
        self.poller.register(sys.stdin.buffer, uselect.POLLIN)
        return self

    def __exit__(self, type, value, traceback):
        self.poller.unregister(sys.stdin.buffer)

    @property
    def ch(self):
        
        if self.poller.poll(0):
            b = sys.stdin.buffer.read(1)
            
            if b == self.ESC:
                b = b'ESC'
                if self.poller.poll(0):
                    b = sys.stdin.buffer.read(2)
                    b = self.EXT_CODE_TBL.get(b, b'UNKNOWN')
            else:
                b = self.EXT_CODE_TBL.get(b, b)

            return b.decode()


#------------------------------------------------------------------------------------------------------
# input function
#------------------------------------------------------------------------------------------------------

def input(prompt:str="") -> str:
    @micropython.native
    def __char_width(ch: str) -> int:
        return 1 if len(ch.encode('utf-8')) == 1 else 2

    repl_in = usys.stdin.buffer
    repl_out = usys.stdout
    
    BACKSPACE = (0x08, 0x7F)
    ENTER = (0x0D, 0x0A)
        
    if prompt:
        repl_out.write(prompt.encode('utf-8'))

    buf = []
    pos = 0
    push = None
    
    while True:
        if push is not None:
            b = push
            push = None
        else:
            while not uselect.select([repl_in], [], [], 0)[0]:
                pass
            b = repl_in.read(1)
            if not b:
                continue
        byte = b[0]

        if byte in ENTER:
            repl_out.write(b"\n")
            while uselect.select([repl_in], [], [], 0)[0]:
                nxt = repl_in.read(1)
                if not nxt:
                    continue
                if nxt[0] in ENTER:
                    continue
                push = nxt
                break
            break

        if byte == 0x1B:
            # Read escape sequence
            seq = repl_in.read(1)
            if not seq:
                continue
            
            # Check for CSI sequence (ESC [)
            if seq[0] == 0x5B:  # '['
                # Read next byte(s)
                cmd = repl_in.read(1)
                if not cmd:
                    continue
                
                cmd_byte = cmd[0]
                
                # Arrow keys and basic navigation
                if cmd_byte == 0x44:  # 'D' - Left arrow
                    if pos > 0:
                        w = __char_width(buf[pos-1])
                        repl_out.write(f"\x1b[{w}D".encode())
                        pos -= 1
                elif cmd_byte == 0x43:  # 'C' - Right arrow
                    if pos < len(buf):
                        w = __char_width(buf[pos])
                        repl_out.write(f"\x1b[{w}C".encode())
                        pos += 1
                elif cmd_byte == 0x41:  # 'A' - Up arrow (ignore for now)
                    pass
                elif cmd_byte == 0x42:  # 'B' - Down arrow (ignore for now)
                    pass
                elif cmd_byte == 0x48:  # 'H' - Home
                    if pos > 0:
                        total_w = sum(__char_width(c) for c in buf[:pos])
                        repl_out.write(f"\x1b[{total_w}D".encode())
                        pos = 0
                elif cmd_byte == 0x46:  # 'F' - End
                    if pos < len(buf):
                        total_w = sum(__char_width(c) for c in buf[pos:])
                        repl_out.write(f"\x1b[{total_w}C".encode())
                        pos = len(buf)
                # Extended keys (Del, Insert, etc.)
                elif cmd_byte in (0x32, 0x33):  # '2' (Insert) or '3' (Delete)
                    tilde = repl_in.read(1)
                    if tilde and tilde[0] == 0x7E:  # '~'
                        if cmd_byte == 0x33 and pos < len(buf):  # Delete key
                            removed = buf.pop(pos)
                            repl_out.write(b"\x1b[K")
                            tail = ''.join(buf[pos:])
                            if tail:
                                repl_out.write(tail.encode('utf-8'))
                                ws = sum(__char_width(c) for c in tail)
                                repl_out.write(f"\x1b[{ws}D".encode())
            continue

        # Backspace
        if byte in BACKSPACE and pos > 0:
            pos -= 1
            removed = buf.pop(pos)
            w = __char_width(removed)
            repl_out.write(f"\x1b[{w}D".encode())
            repl_out.write(b"\x1b[K")
            tail = ''.join(buf[pos:])
            if tail:
                repl_out.write(tail.encode('utf-8'))
                ws = sum(__char_width(c) for c in tail)
                repl_out.write(f"\x1b[{ws}D".encode())
            continue

        first = byte
        if first < 0x80:
            seq = b
        elif (first & 0xE0) == 0xC0:
            seq = b + repl_in.read(1)
        elif (first & 0xF0) == 0xE0:
            seq = b + repl_in.read(2)
        elif (first & 0xF8) == 0xF0:
            seq = b + repl_in.read(3)
        else:
            continue

        try:
            ch = seq.decode('utf-8')
        except UnicodeError:
            continue

        buf.insert(pos, ch)
        w = __char_width(ch)
        tail = ''.join(buf[pos+1:])

        repl_out.write(seq)
        if tail:
            repl_out.write(tail.encode('utf-8'))
            ws = sum(__char_width(c) for c in tail)
            repl_out.write(f"\x1b[{ws}D".encode())
        pos += 1

    return ''.join(buf)


_wifi_iface = None

class WifiManager:
    @staticmethod
    def _ensure_initialized():
        global _wifi_iface
        if _wifi_iface is None:
            _wifi_iface = network.WLAN(network.STA_IF)
            if not _wifi_iface.active():
                _wifi_iface.active(True)

    @staticmethod
    def scan() -> list[tuple[str,int,int,int]]:
        WifiManager._ensure_initialized()
        return _wifi_iface.scan()

    @staticmethod
    def available_ssids() -> list[str]:
        WifiManager._ensure_initialized()
        aps = _wifi_iface.scan()
        ssids = set()
        for ap in aps:
            ssid = ap[0].decode('utf-8', 'ignore')
            if ssid:
                ssids.add(ssid)
        return list(ssids)

    @staticmethod
    def connect(ssid: str, password: str, timeout: float = 20.0) -> bool:
        WifiManager._ensure_initialized()
        if _wifi_iface.isconnected():
            return True

        _wifi_iface.connect(ssid, password)
        start = utime.ticks_ms()
        while not _wifi_iface.isconnected():
            if utime.ticks_diff(utime.ticks_ms(), start) > int(timeout * 1000):
                return False
            utime.sleep_ms(200)
        return True

    @staticmethod
    def disconnect() -> None:
        WifiManager._ensure_initialized()
        if _wifi_iface.isconnected():
            _wifi_iface.disconnect()
            utime.sleep_ms(100)
    
    @staticmethod
    def ifconfig() -> tuple | None:
        if not WifiManager.is_connected():
            return None
        return _wifi_iface.ifconfig()

    @staticmethod
    def is_connected() -> bool:
        WifiManager._ensure_initialized()
        return _wifi_iface.isconnected()

    @staticmethod
    def ip() -> str | None:
        if not WifiManager.is_connected():
            return None
        return _wifi_iface.ifconfig()[0]


class BLEBroker:
    _IRQ_CENTRAL_CONNECT    = micropython.const(1)
    _IRQ_CENTRAL_DISCONNECT = micropython.const(2)
    _IRQ_GATTS_WRITE        = micropython.const(3)

    _FLAG_READ              = micropython.const(0x0002)
    _FLAG_WRITE             = micropython.const(0x0008)
    _FLAG_NOTIFY            = micropython.const(0x0010)

    _MAX_QUEUE              = micropython.const(32)
    _MAX_CONNECTIONS        = micropython.const(4)
    _MAX_MESSAGE_SIZE       = micropython.const(512)
    _MAX_TOPIC_LENGTH       = micropython.const(64)

    def __init__(self, name="TiCLE_BLEBroker", *,
                 service_uuid="12345678-0000-0000-0000-000000000010",
                 char_uuid="12345678-0000-0000-0000-000000000011",
                 max_connections=4):
        if not (1 <= max_connections <= self._MAX_CONNECTIONS):
            raise ValueError(f"max_connections must be 1-{self._MAX_CONNECTIONS}")
        
        if len(name) > 29:
            raise ValueError("BLE name must be <= 29 characters")
        
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)

        self._name = name
        self._max_connections = max_connections
        self._connections = set()
        self._subs = set()
        self._queue = []
        self._in_dispatch = False
        self._active = True
        self._dropped_events = 0
        self._service_uuid = bluetooth.UUID(service_uuid)
        self._char_uuid = bluetooth.UUID(char_uuid)

        ((self._char_handle,),) = self._ble.gatts_register_services((
            (self._service_uuid, ((self._char_uuid, self._FLAG_READ | self._FLAG_WRITE | self._FLAG_NOTIFY),)),
        ))

        self._advertise()

        self._on_connect = None
        self._on_disconnect = None
        self._on_publish = None
        self._on_subscribe = None
        self._on_message = None
        self._on_error = None

    @property
    def on_connect(self): 
        return self._on_connect

    @on_connect.setter
    def on_connect(self, cb): 
        self._on_connect = cb

    @property
    def on_disconnect(self): 
        return self._on_disconnect
    
    @on_disconnect.setter
    def on_disconnect(self, cb): 
        self._on_disconnect = cb

    @property
    def on_publish(self): 
        return self._on_publish

    @on_publish.setter
    def on_publish(self, cb): 
        self._on_publish = cb

    @property
    def on_subscribe(self): 
        return self._on_subscribe
    
    @on_subscribe.setter
    def on_subscribe(self, cb): 
        self._on_subscribe = cb

    @property
    def on_message(self): 
        return self._on_message

    @on_message.setter
    def on_message(self, cb): 
        self._on_message = cb

    @property
    def on_error(self):
        return self._on_error

    @on_error.setter
    def on_error(self, cb):
        self._on_error = cb

    @property
    def is_active(self) -> bool:
        return self._active and self._ble.active()

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    @property
    def subscribed_topics(self) -> list:
        return list(self._subs)

    @property
    def dropped_event_count(self) -> int:
        return self._dropped_events

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.deinit()

    def deinit(self):
        if not self._active:
            return
        
        try:
            self._active = False
            self._ble.gap_advertise(None)
            
            for conn in list(self._connections):
                try:
                    self._ble.gap_disconnect(conn)
                except:
                    pass
            
            self._connections.clear()
            self._queue.clear()
            self._subs.clear()
            self._ble.active(False)
        except Exception as e:
            self._error_callback("deinit_error", str(e))

    def _error_callback(self, error_type, details):
        if self._on_error:
            try:
                self._on_error(error_type, details)
            except:
                pass
        else:
            print(f"[BLE] {error_type}: {details}")

    def _irq(self, event, data):
        if not self._active:
            return
        
        if len(self._queue) >= self._MAX_QUEUE:
            self._queue.pop(0)
            self._dropped_events += 1
            if self._dropped_events == 1 or self._dropped_events % 10 == 0:
                self._error_callback("queue_overflow", f"Dropped {self._dropped_events} events")

        self._queue.append((event, data))
        if not self._in_dispatch:
            self._in_dispatch = True
            micropython.schedule(self._dispatch, None)

    def _dispatch(self, _):
        while self._queue:
            try:
                event, data = self._queue.pop(0)
            except IndexError:
                break
            
            try:
                if event == self._IRQ_CENTRAL_CONNECT:
                    conn_handle, _, _ = data
                    
                    if len(self._connections) >= self._max_connections:
                        self._error_callback("connection_limit", f"Rejecting connection (max {self._max_connections})")
                        try:
                            self._ble.gap_disconnect(conn_handle)
                        except:
                            pass
                        continue
                    
                    self._connections.add(conn_handle)
                    if self._on_connect:
                        self._safe_call(self._on_connect)

                elif event == self._IRQ_CENTRAL_DISCONNECT:
                    conn_handle, _, _ = data
                    self._connections.discard(conn_handle)
                    if self._on_disconnect:
                        self._safe_call(self._on_disconnect)
                    
                    if self._active:
                        self._advertise()

                elif event == self._IRQ_GATTS_WRITE:
                    conn_handle, attr_handle = data
                    if attr_handle == self._char_handle:
                        try:
                            raw = self._ble.gatts_read(self._char_handle)
                            msg = raw.decode('utf-8', 'ignore').strip()
                            if msg:
                                self._handle_message(msg)
                        except Exception as e:
                            self._error_callback("decode_error", str(e))

            except Exception as e:
                self._error_callback("dispatch_error", str(e))

        self._in_dispatch = False  

    def _handle_message(self, msg):
        try:
            if ":" in msg:
                topic, payload = msg.split(":", 1)
            else:
                topic, payload = msg, ""
            
            if not topic:
                self._error_callback("invalid_message", "Empty topic")
                return
            
            if topic in self._subs and self._on_message:
                self._safe_call(self._on_message, topic, payload)
        except Exception as e:
            self._error_callback("message_handler_error", str(e))

    def subscribe(self, topic):
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")
        
        if ':' in topic:
            raise ValueError("Topic must not contain ':' character")
        
        if len(topic) > self._MAX_TOPIC_LENGTH:
            raise ValueError(f"Topic too long (max {self._MAX_TOPIC_LENGTH} chars)")
        
        self._subs.add(topic)
        if self._on_subscribe:
            self._safe_call(self._on_subscribe, topic)
        return True

    def unsubscribe(self, topic):
        if topic in self._subs:
            self._subs.discard(topic)
            return True
        return False

    def publish(self, topic, message):
        if not isinstance(topic, str) or not topic:
            raise ValueError("Topic must be a non-empty string")
        
        if ':' in topic:
            raise ValueError("Topic must not contain ':' character")
        
        if not isinstance(message, str):
            message = str(message)
        
        try:
            frame = f"{topic}:{message}".encode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encode message: {e}")
        
        if len(frame) > self._MAX_MESSAGE_SIZE:
            raise ValueError(f"Message too large: {len(frame)} > {self._MAX_MESSAGE_SIZE} bytes")
        
        failed_conns = []
        for conn in self._connections:
            try:
                self._ble.gatts_notify(conn, self._char_handle, frame)
            except Exception as e:
                failed_conns.append(conn)
                self._error_callback("notify_error", f"conn {conn}: {e}")
        
        for conn in failed_conns:
            self._connections.discard(conn)
        
        if self._on_publish:
            self._safe_call(self._on_publish, topic, message)

    def _safe_call(self, cb, *a):
        try:
            cb(*a)
        except Exception as e:
            self._error_callback("callback_error", str(e))

    def _advertise(self, interval_us=500000):
        if not self._active:
            return
        
        try:
            payload = self._advertising_payload(name=self._name, services=[self._service_uuid])
            self._ble.gap_advertise(interval_us, adv_data=payload)
        except Exception as e:
            self._error_callback("advertise_error", str(e))

    @staticmethod
    def _advertising_payload(name=None, services=None):
        payload = bytearray()

        def _append(adv_type, value):
            payload.extend(ustruct.pack("BB", len(value) + 1, adv_type))
            payload.extend(value)

        _append(0x01, ustruct.pack("B", 0x06))
        if name:
            _append(0x09, name.encode())
        if services:
            for uuid in services:
                b = bytes(uuid)
                _append(0x07 if len(b) == 16 else 0x03, b)
        return payload


class Led(machine.Pin):
    def __init__(self):
        super().__init__("WL_GPIO0", machine.Pin.OUT)


class Button:
    @staticmethod
    def read() -> bool:
        return rp2.bootsel_button() == 1



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
        self._edge_config = [0] * n  # No edge detection by default
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
    LOGIC_HIGH  = True   # Active High: HIGH = active
    LOGIC_LOW   = False  # Active Low: LOW = active
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
                    pin.value(0)  # Active high: LOW = inactive
                else:
                    pin.value(1)  # Active low: HIGH = inactive
            
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
        self._period_ms = [20] * n  # 0 = disabled
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
            self._pwm[i].duty_u16(0)  # Start with 0% duty for safety

    def deinit(self) -> None:
        try:
            for pwm in self._pwm:
                pwm.duty_u16(0)
            
            utime.sleep_ms(50)  # Allow hardware to settle
            
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


#------------------------------------------------------------------------------------------------------
# I2c bus scanner
#------------------------------------------------------------------------------------------------------

def i2cdetect(*, 
              id: int | None = None, 
              sda: int | None = None, 
              scl: int | None = None, 
              deny_pairs: set | None = None, 
              show: bool = False) -> list | None:
    I2C_PIN_MAP = {
        0: ((0, 1), (4, 5), (8, 9), (12, 13), (16, 17), (20, 21)),
        1: ((2, 3), (6, 7), (10, 11), (14, 15), (18, 19), (26, 27)),
    }

    def _check(i2c_id, sda_pin, scl_pin):
        try:
            i2c = machine.I2C(id=i2c_id, sda=machine.Pin(sda_pin), scl=machine.Pin(scl_pin), freq=100_000)
            return i2c.scan()
        except Exception:
            return []
        finally:
            try:
                machine.Pin(scl_pin, machine.Pin.IN)
                machine.Pin(sda_pin, machine.Pin.IN)
            except Exception:
                pass

    def _add_plan(plan, seen, i2c_id, sda_pin, scl_pin):
        key = (i2c_id, sda_pin, scl_pin)
        if key in seen:
            return
        if deny_pairs and (sda_pin, scl_pin) in deny_pairs:
            return
        plan.append(key)
        seen.add(key)

    plan = []
    seen = set()

    if sda is not None and scl is not None:
        if id is None:
            ids_containing = [i for i, pairs in I2C_PIN_MAP.items() if (sda, scl) in pairs]
            ids_others     = [i for i in I2C_PIN_MAP.keys() if i not in ids_containing]
            try_ids = ids_containing + ids_others or [0, 1]
            for i2c_id in try_ids:
                _add_plan(plan, seen, i2c_id, sda, scl)
        else:
            if id in I2C_PIN_MAP and (sda, scl) in I2C_PIN_MAP[id]:
                _add_plan(plan, seen, id, sda, scl)
            else:
                _add_plan(plan, seen, id, sda, scl)
                for p in I2C_PIN_MAP.get(id, ()):
                    if p == (sda, scl):
                        continue
                    _add_plan(plan, seen, id, p[0], p[1])
    elif id is not None:
        for p in I2C_PIN_MAP.get(id, ()):
            _add_plan(plan, seen, id, p[0], p[1])
    else:
        for i2c_id, pairs in I2C_PIN_MAP.items():
            for p in pairs:
                _add_plan(plan, seen, i2c_id, p[0], p[1])

    if not plan:
        return []

    found_any = []

    for i2c_id, sda_pin, scl_pin in plan:
        devices = _check(i2c_id, sda_pin, scl_pin)
        if not devices:
            continue

        found_any.append(((sda_pin, scl_pin), devices))

        if show:
            print(f"I2C{i2c_id} on SDA={sda_pin}, SCL={scl_pin}: {len(devices)} device(s) found")
            print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
            for i in range(0, 8):
                print("{:02x}:".format(i * 16), end='')
                for j in range(0, 16):
                    address = i * 16 + j
                    if address in devices:
                        print(Color.FG.BRIGHT_YELLOW + " {:02x}".format(address) + Color.RESET, end='')
                    else:
                        print(" --", end='')
                print()

    return found_any


#------------------------------------------------------------------------------------------------------
# Bus status
#------------------------------------------------------------------------------------------------------

STAT_OK        = micropython.const(0)
STAT_TIMEOUT   = micropython.const(1 << 0)
STAT_BUS_ERR   = micropython.const(1 << 1)
STAT_NO_DEVICE = micropython.const(1 << 2)

#------------------------------------------------------------------------------------------------------
# SpinLock class
#------------------------------------------------------------------------------------------------------

I2C0_SPINLOCK_ID = micropython.const(30)
I2C1_SPINLOCK_ID = micropython.const(31)
SPI0_SPINLOCK_ID = micropython.const(32)
SPI1_SPINLOCK_ID = micropython.const(33)

_SPINLOCK_BASE  = micropython.const(0xD0000100)  # SPINLOCK0

class SpinLock:
    __slots__ = ("_addr", "_polite", "_yield_every")

    def __init__(self, *, lock_id: int, polite: bool = False, yield_every: int = 64):
        if not (0 <= lock_id <= 31):
            raise ValueError("lock_id must be 0..31")
        self._addr = _SPINLOCK_BASE + (lock_id << 2)
        self._polite = polite
        self._yield_every = yield_every if yield_every > 0 else 64

    def acquire(self) -> None:
        addr = self._addr
        if not self._polite:
            while not machine.mem32[addr]:
                pass
        else:
            cnt = 0
            while not machine.mem32[addr]:
                cnt += 1
                if cnt >= self._yield_every:
                    cnt = 0
                    try:
                        machine.idle()
                    except:
                        utime.sleep_us(1)

    def release(self) -> None:
        machine.mem32[self._addr] = 1

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, et, ev, tb):
        self.release()


#------------------------------------------------------------------------------------------------------
# I2CMaster
#------------------------------------------------------------------------------------------------------

_I2C_PIN_MAP =  {
    0: {'sda': {0, 4, 8, 12, 16, 20}, 'scl': {1, 5, 9, 13, 17, 21}},
    1: {'sda': {2, 6, 10, 14, 18, 26}, 'scl': {3, 7, 11, 15, 19, 27}},
}

class I2CMaster:
    __slots__ = (
        "_id","_scl","_sda","_timeout_us","_freq","_i2c","_lock",
        "_retry_retries","_retry_delay_us","_b1","_b2","_stats_last_err"
    )

    def __init__(self, *, sda:int, scl:int, freq:int=400_000, timeout_us:int=50_000):
        self._id = self._infer_bus_id_from_pins(sda, scl)
        self._scl, self._sda = scl, sda
        self._freq = freq
        self._timeout_us = timeout_us
        self._retry_retries = 1
        self._retry_delay_us = 200
        self._b1 = bytearray(1)
        self._b2 = bytearray(2)
        self._stats_last_err = STAT_OK
        self._lock = SpinLock(lock_id=(I2C0_SPINLOCK_ID if self._id == 0 else I2C1_SPINLOCK_ID))

        self._i2c = machine.I2C(self._id, scl=machine.Pin(self._scl), sda=machine.Pin(self._sda), freq=self._freq, timeout=self._timeout_us)

    @property
    def bus_id(self) -> int:
        return self._id

    @property
    def pins(self):
        return (self._sda, self._scl)

    @property
    def last_error(self) -> int:
        return self._stats_last_err

    def __repr__(self):
        return f"<I2CMaster id={self._id} sda={self._sda} scl={self._scl} freq={self._freq} timeout_us={self._timeout_us}>"

    def set_retry_policy(self, *, retries:int=None, delay_us:int=None):
        if retries is not None: 
            self._retry_retries = max(0, int(retries))
        
        if delay_us is not None: 
            self._retry_delay_us = max(0, int(delay_us))

    def set_timeout(self, timeout_us:int):
        self._timeout_us = max(0, int(timeout_us))
        self._acquire()
        try:
            self._i2c.init(freq=self._freq, timeout=self._timeout_us)
        except (TypeError, AttributeError):
            self._i2c = machine.I2C(self._id, scl=machine.Pin(self._scl), sda=machine.Pin(self._sda), freq=self._freq, timeout=self._timeout_us)
        finally:
            self._release()

    def set_freq(self, freq:int):
        if freq <= 0:
            raise ValueError("freq must be > 0")
        self._acquire()
        self._freq = freq
        try:
            self._i2c.init(freq=self._freq, timeout=self._timeout_us)
        except (TypeError, AttributeError):
            self._i2c = machine.I2C(self._id, scl=machine.Pin(self._scl), sda=machine.Pin(self._sda), freq=self._freq, timeout=self._timeout_us)
        finally:
            self._release()
 
    def scoped_freq(self, freq:int):
        class _Ctx:
            def __init__(self, m, f): 
                self.m, self.f, self.prev = m, f, None
            
            def __enter__(self):
                self.prev = self.m._freq
                if self.f is not None and self.f != self.prev:
                    self.m.set_freq(self.f)
                return self.m
            
            def __exit__(self, et, ev, tb):
                if self.prev is not None and self.prev != self.m._freq:
                    self.m.set_freq(self.prev)
        
        return _Ctx(self, freq)

    def deinit(self):
        try: self._i2c.deinit()
        except AttributeError: pass

    def _infer_bus_id_from_pins(self, sda, scl):
        for _id, pins in _I2C_PIN_MAP.items():
            if sda in pins['sda'] and scl in pins['scl']:
                return _id
        raise ValueError("Invalid I2C pins for RP2350 map: SDA={}, SCL={}".format(sda, scl))

    def _with_retry(self, fn, *a, retries=None, delay_us=None, **kw):
        r = self._retry_retries if retries is None else retries
        d = self._retry_delay_us if delay_us is None else delay_us
        last = None
        for i in range(r + 1):
            try:
                out = fn(*a, **kw)
                self._stats_last_err = STAT_OK
                return out
            except OSError as e:
                last = f"The device is not recognized: {e}"
                if i == r:
                    self._stats_last_err = STAT_BUS_ERR
                    raise
                utime.sleep_us(d)
        raise last

    def _validate_addr(self, addr:int):
        if not (0 <= addr <= 0x7F):
            raise ValueError("I2C 7-bit address required (0..0x7F)")

    def _validate_addrsize(self, sz:int):
        if sz not in (8, 16):
            raise ValueError("addrsize must be 8 or 16")

    def _validate_reg(self, reg:int, addrsize:int):
        if addrsize == 8 and not (0 <= reg <= 0xFF):
            raise ValueError("reg out of range for 8-bit addrsize")
        if addrsize == 16 and not (0 <= reg <= 0xFFFF):
            raise ValueError("reg out of range for 16-bit addrsize")

    def _acquire(self):
        self._lock.acquire()

    def _release(self):
        self._lock.release()

    def probe(self, addr:int) -> bool:
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto, addr, b"", stop=True)
            return True
        except OSError:
            return False
        finally:
            self._release()

    def readfrom(self, addr:int, nbytes:int, *, stop:bool=True) -> bytes:
        self._validate_addr(addr)
        self._acquire()
        try:
            return self._with_retry(self._i2c.readfrom, addr, nbytes, stop=stop)
        finally:
            self._release()

    def readfrom_into(self, addr:int, buf, *, stop:bool=True) -> None:
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.readfrom_into, addr, buf, stop=stop)
        finally:
            self._release()

    def writeto(self, addr:int, buf, *, stop:bool=True) -> int:
        self._validate_addr(addr)
        self._acquire()
        try:
            return self._with_retry(self._i2c.writeto, addr, buf, stop=stop)
        finally:
            self._release()

    def readfrom_mem(self, addr:int, reg:int, nbytes:int, *, addrsize:int=8) -> bytes:
        self._validate_addr(addr); self._validate_addrsize(addrsize); self._validate_reg(reg, addrsize)
        self._acquire()
        try:
            return self._with_retry(self._i2c.readfrom_mem, addr, reg, nbytes, addrsize=addrsize)
        finally:
            self._release()

    def readfrom_mem_into(self, addr:int, reg:int, buf, *, addrsize:int=8) -> None:
        self._validate_addr(addr); self._validate_addrsize(addrsize); self._validate_reg(reg, addrsize)
        self._acquire()
        try:
            self._with_retry(self._i2c.readfrom_mem_into, addr, reg, buf, addrsize=addrsize)
        finally:
            self._release()

    def writeto_mem(self, addr:int, reg:int, buf, *, addrsize:int=8) -> None:
        self._validate_addr(addr); self._validate_addrsize(addrsize); self._validate_reg(reg, addrsize)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto_mem, addr, reg, buf, addrsize=addrsize)
        finally:
            self._release()

    def read_u8(self, addr:int, reg:int, *, addrsize:int=8) -> int:
        self._validate_addr(addr)
        self.readfrom_mem_into(addr, reg, self._b1, addrsize=addrsize)
        return self._b1[0]

    def read_u16(self, addr:int, reg:int, *, little_endian:bool=True, addrsize:int=8) -> int:
        self._validate_addr(addr)
        self.readfrom_mem_into(addr, reg, self._b2, addrsize=addrsize)
        return (self._b2[0] | (self._b2[1] << 8)) if little_endian else ((self._b2[0] << 8) | self._b2[1])

    def write_u8(self, addr:int, reg:int, val:int, *, addrsize:int=8) -> None:
        self._validate_addr(addr)
        self._b1[0] = val & 0xFF
        self.writeto_mem(addr, reg, self._b1, addrsize=addrsize)

    def write_u16(self, addr:int, reg:int, val:int, *, little_endian:bool=True, addrsize:int=8) -> None:
        self._validate_addr(addr)
        v = val & 0xFFFF
        if little_endian:
            self._b2[0], self._b2[1] = (v & 0xFF), ((v >> 8) & 0xFF)
        else:
            self._b2[0], self._b2[1] = ((v >> 8) & 0xFF), (v & 0xFF)
        self.writeto_mem(addr, reg, self._b2, addrsize=addrsize)

    def write_mem_ex(self, addr:int, reg_bytes:bytes, payload:bytes, *, stop:bool=True) -> None:
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto, addr, reg_bytes, stop=False)
            self._with_retry(self._i2c.writeto, addr, payload, stop=stop)
        finally:
            self._release()

    def read_mem_ex(self, addr:int, reg_bytes:bytes, n:int, out:bytearray=None):
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto, addr, reg_bytes, stop=False)
            if out is None:
                return self._with_retry(self._i2c.readfrom, addr, n, stop=True)
            else:
                self._with_retry(self._i2c.readfrom_into, addr, out, stop=True)
                return None
        finally:
            self._release()

#------------------------------------------------------------------------------------------------------
# Spi class
#------------------------------------------------------------------------------------------------------

class _CSCtx:
    __slots__ = ("_spi",)
    def __init__(self, spi): 
        self._spi = spi

    def __enter__(self):
        s = self._spi
        s._acquire()
        if s._ctx_depth == 0:
            s._assert_cs()
        s._ctx_depth += 1
        return s

    def __exit__(self, et, ev, tb):
        s = self._spi
        s._ctx_depth -= 1
        if s._ctx_depth == 0:
            s._deassert_cs()
        s._release()



_SPI_PIN_MAP = {
    0: {
        'miso': {0, 4, 16},  # RX
        'cs':   {1, 5, 17},
        'sck':  {2, 6, 18},
        'mosi': {3, 7, 19},  # TX
    },
    1: {
        'mosi': { 8, 12},    # TX
        'cs':   { 9, 13},
        'sck':  {10, 14},
        'miso': {11, 15},    # RX
    },
}

class Spi:
    __slots__ = (
        "_id", "_sck","_mosi","_miso","_cs_active_low","_cs",
        "_baudrate","_polarity","_phase","_bits","_firstbit",
        "_lock","_retry_retries","_retry_delay_us",
        "_stats_last_err","_b1", "_spi",
        "_lock_depth","_ctx_depth",
    )

    def __init__(self, *,
                 sck:int=None, mosi:int=None, miso:int=None,
                 cs:int=None, cs_active_low:bool=True,
                 baudrate:int=10_000_000, polarity:int=0, phase:int=0,
                 bits:int=8, firstbit:int=None):
        if firstbit is None:
            firstbit = getattr(machine.SPI, "MSB", 0)
        if sck is None or mosi is None or miso is None or cs is None:
            raise ValueError("sck/mosi/miso/cs required")
        if len({sck, mosi, miso, cs}) != 4:
            raise ValueError("sck/mosi/miso/cs must be distinct pins")

        self._id = self._infer_bus_id_from_pins(sck, mosi, miso)
        if cs not in _SPI_PIN_MAP[self._id]['cs']:
            raise ValueError("CS pin %d not valid for SPI%d" % (cs, self._id))
        self._sck, self._mosi, self._miso = sck, mosi, miso

        self._cs = machine.Pin(cs, machine.Pin.OUT)
        self._cs_active_low = cs_active_low
        self._set_cs_inactive()

        self._baudrate = baudrate
        self._polarity = polarity
        self._phase    = phase
        self._bits     = bits
        self._firstbit = firstbit
        self._lock = SpinLock(lock_id=SPI0_SPINLOCK_ID if self._id == 0 else SPI1_SPINLOCK_ID)
        self._retry_retries  = 1
        self._retry_delay_us = 200
        self._stats_last_err = STAT_OK
        self._b1 = bytearray(1)

        self._spi = machine.SPI(self._id,
                                sck=machine.Pin(self._sck),
                                mosi=machine.Pin(self._mosi),
                                miso=machine.Pin(self._miso),
                                baudrate=self._baudrate,
                                polarity=self._polarity,
                                phase=self._phase,
                                bits=self._bits,
                                firstbit=self._firstbit)

        self._lock_depth = 0
        self._ctx_depth  = 0

    def _infer_bus_id_from_pins(self, sck, mosi, miso):
        for _id, pins in _SPI_PIN_MAP.items():
            if (sck in pins['sck']) and (mosi in pins['mosi']) and (miso in pins['miso']):
                return _id
        raise ValueError("Invalid SPI pins for RP2350 map: SCK={}, MOSI={}, MISO={}".format(sck, mosi, miso))

    def _with_retry(self, fn, *a, retries=None, delay_us=None, **kw):
        r = self._retry_retries if retries is None else retries
        d = self._retry_delay_us if delay_us is None else delay_us
        last = None
        for i in range(r+1):
            try:
                out = fn(*a, **kw)
                self._stats_last_err = STAT_OK
                return out
            except OSError as e:
                last = e
                if i == r:
                    self._stats_last_err = STAT_BUS_ERR
                    raise
                utime.sleep_us(d)
        raise last

    def _acquire(self):
        if self._lock_depth == 0:
            self._lock.acquire()
        self._lock_depth += 1

    def _release(self):
        if self._lock_depth <= 0:
            return
        self._lock_depth -= 1
        if self._lock_depth == 0:
            self._lock.release()

    def _set_cs_active(self):
        self._cs.value(0 if self._cs_active_low else 1)

    def _set_cs_inactive(self):
        self._cs.value(1 if self._cs_active_low else 0)

    def _assert_cs(self):
        self._set_cs_active()

    def _deassert_cs(self):
        self._set_cs_inactive()

    @property
    def bus_id(self): 
        return self._id
    
    @property
    def pins(self):   
        return (self._sck, self._mosi, self._miso)

    @property
    def cs_pin(self):
        return self._cs

    @property
    def last_error(self) -> int:
        return self._stats_last_err

    def __repr__(self):
        cs_id = self._cs.id()
        fb = "MSB" if self._firstbit == getattr(machine.SPI, "MSB", 0) else "LSB"
        return ("<Spi id=%d sck=%s mosi=%s miso=%s cs=%s baud=%d pol=%d pha=%d bits=%d firstbit=%s>" %
                (self._id, self._sck, self._mosi, self._miso, cs_id,
                 self._baudrate, self._polarity, self._phase, self._bits, fb))

    def set_retry_policy(self, *, retries:int=None, delay_us:int=None):
        if retries is not None:
            if retries < 0: raise ValueError("retries must be >= 0")
            self._retry_retries = retries
        if delay_us is not None:
            if delay_us < 0: raise ValueError("delay_us must be >= 0")
            self._retry_delay_us = delay_us

    def deinit(self):
        try: 
            self._set_cs_inactive()
        except Exception: 
            pass
        try: 
            self._spi.deinit()
        except AttributeError: 
            pass

    def reinit(self, *, baudrate=None, polarity=None, phase=None, bits=None, firstbit=None):
        self._set_cs_inactive()
        
        if baudrate is not None: 
            self._baudrate = baudrate
        if polarity is not None: 
            self._polarity = polarity
        if phase is not None: 
            self._phase    = phase
        if bits is not None: 
            self._bits     = bits
        if firstbit is not None: 
            self._firstbit = firstbit
        try:
            self._spi.init(baudrate=self._baudrate, polarity=self._polarity, phase=self._phase, bits=self._bits, firstbit=self._firstbit)
        except AttributeError:
            self._spi.deinit()
            self._spi = machine.SPI(self._id,
                                    sck=machine.Pin(self._sck),
                                    mosi=machine.Pin(self._mosi),
                                    miso=machine.Pin(self._miso),
                                    baudrate=self._baudrate,
                                    polarity=self._polarity,
                                    phase=self._phase,
                                    bits=self._bits,
                                    firstbit=self._firstbit)

    def select(self):
        self._acquire()
        self._assert_cs()

    def deselect(self):
        self._deassert_cs()
        self._release()

    def selected(self):
        return _CSCtx(self)

    def write(self, buf, *, hold_cs:bool=False):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write, buf)
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._deassert_cs()
        finally:
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._release()

    def readinto(self, buf, *, write:int=0xFF, hold_cs:bool=False):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.readinto, buf, write)
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._deassert_cs()
        finally:
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._release()

    def read(self, n:int, *, write:int=0xFF) -> bytes:
        self._acquire()
        try:
            self._assert_cs()
            data = self._with_retry(self._spi.read, n, write)
            if self._ctx_depth == 0:
                self._deassert_cs()
            return data
        finally:
            if self._ctx_depth == 0:
                self._release()

    def write_readinto(self, wbuf, rbuf, *, hold_cs:bool=False):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write_readinto, wbuf, rbuf)
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._deassert_cs()
        finally:
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._release()

    def write_then_readinto(self, cmd_bytes, rx_buf, *, dummy:int=0xFF):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write, cmd_bytes)
            self._with_retry(self._spi.readinto, rx_buf, dummy)
            if self._ctx_depth == 0:
                self._deassert_cs()
        finally:
            if self._ctx_depth == 0:
                self._release()

    def write_then_write(self, cmd_bytes, payload_bytes):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write, cmd_bytes)
            self._with_retry(self._spi.write, payload_bytes)
            if self._ctx_depth == 0:
                self._deassert_cs()
        finally:
            if self._ctx_depth == 0:
                self._release()

    def write_u8(self, v:int):
        self._b1[0] = v & 0xFF
        self.write(self._b1)

    def read_u8(self) -> int:
        self.readinto(self._b1)
        return self._b1[0]


#------------------------------------------------------------------------------------------------------
# ReplSerial class
#------------------------------------------------------------------------------------------------------

class ReplSerial:
    def __init__(self, timeout:float|None=None, *, bufsize:int=512, poll_ms:int=10):
        self._timeout   = timeout
        self._stdin     = usys.stdin.buffer
        self._stdout    = usys.stdout
        self._buf       = RingBuffer(bufsize)
        self._scheduled = False
        self._tmr = machine.Timer(-1)
        self._tmr.init(period=poll_ms, mode=machine.Timer.PERIODIC, callback=self.__tick)

    def __tick(self, t):
        if not self._scheduled:
            self._scheduled = True
            try:
                micropython.schedule(self.__pump, None)
            except RuntimeError:
                self._scheduled = False

    def __pump(self, _):
        try:
            # read 1 byte at a time as long as data is ready
            while uselect.select([self._stdin], [], [], 0)[0]:
                b = self._stdin.read(1)
                if not b:
                    break
                self._buf.put(b)
        except Exception:
            pass
        finally:
            self._scheduled = False

    def __wait(self, deadline_ms:int):
        while not self._buf.avail():
            if deadline_ms is not None and utime.ticks_diff(deadline_ms, utime.ticks_ms()) <= 0:
                return
            dur = None if deadline_ms is None else max(0,
                utime.ticks_diff(deadline_ms, utime.ticks_ms())) / 1000
            uselect.select([self._stdin], [], [], dur)

    @property
    def timeout(self) -> float|None:
        return self._timeout
    
    @timeout.setter
    def timeout(self, value:float|None):
        self._timeout = value

    def read(self, size:int=1) -> bytes:
        if size <= 0:
            return b''
        dl = None if self._timeout is None else utime.ticks_add(utime.ticks_ms(), int(self._timeout*1000))
        self.__wait(dl)
        return self._buf.get(size)

    def read_until(self, expected:bytes=b'\r', max_size:int|None=None) -> bytes:
        # Non-blocking shortcut
        if self._timeout == 0:
            if max_size and self._buf.avail() >= max_size:
                return self._buf.get(max_size)
            
            data = self._buf.get_until(expected, max_size)
            return data or b''

        deadline = None
        if self._timeout is not None:
            deadline = utime.ticks_add(utime.ticks_ms(), int(self._timeout * 1000))

        # Main loop for blocking/timeout
        while True:
            if max_size and self._buf.avail() >= max_size:
                return self._buf.get(max_size)

            data = self._buf.get_until(expected, max_size)
            if data is not None:
                return data

            if deadline is not None:
                if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
                    return b''

            # wait for incoming data
            self.__wait(deadline)

    def write(self, data:bytes) -> int:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")
        return self._stdout.write(data)

    def close(self):
        self._tmr.deinit()

