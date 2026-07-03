# @package: ble
# @version: 2.1.0
# @type: core
# @category: communication
# @interface: BLE
# @depends: none
# @platforms: rp2, esp32, nrf
# @tags: ble, bluetooth, wireless, peripheral, central
# @author: PlanXLab Development Team

import bluetooth
import micropython
import struct

class BLEServer:
    _IRQ_CENTRAL_CONNECT    = micropython.const(1)
    _IRQ_CENTRAL_DISCONNECT = micropython.const(2)
    _IRQ_GATTS_WRITE        = micropython.const(3)

    _FLAG_READ               = micropython.const(0x0002)
    _FLAG_WRITE_NO_RESPONSE  = micropython.const(0x0004)  # Write Command (no ATT response)
    _FLAG_WRITE              = micropython.const(0x0008)  # Write Request (with ATT response)
    _FLAG_NOTIFY             = micropython.const(0x0010)

    FLAG_READ                = micropython.const(0x0002)
    FLAG_WRITE_NO_RESPONSE   = micropython.const(0x0004)
    FLAG_WRITE               = micropython.const(0x0008)
    FLAG_NOTIFY              = micropython.const(0x0010)

    _MAX_QUEUE              = micropython.const(32)
    _MAX_CONNECTIONS        = micropython.const(4)
    _MAX_MESSAGE_SIZE       = micropython.const(512)
    _MAX_TOPIC_LENGTH       = micropython.const(64)

    def __init__(self, name="BLEServer", *,
                 service_uuid="12345678-0000-0000-0000-000000000010",
                 char_uuid="12345678-0000-0000-0000-000000000011",
                 char_uuids=None,
                 char_flags=None,
                 max_connections=4):
        if not (1 <= max_connections <= self._MAX_CONNECTIONS):
            raise ValueError(f"max_connections must be 1-{self._MAX_CONNECTIONS}")
        
        if len(name) > 29:
            raise ValueError("BLE name must be <= 29 characters")
        
        self._name = name
        self._max_connections = max_connections
        self._connections = {}
        self._subs = set()
        self._queue = []
        self._in_dispatch = False
        self._active = True
        self._dropped_events = 0
        self._dispatch_cb = self._dispatch
        self._on_connect = None
        self._on_disconnect = None
        self._on_publish = None
        self._on_subscribe = None
        self._on_message = None
        self._on_error = None

        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)

        self._service_uuid = bluetooth.UUID(service_uuid)

        uuid_strs = list(char_uuids) if char_uuids is not None else [char_uuid]
        if len(uuid_strs) == 0:
            raise ValueError("char_uuids must contain at least one UUID")
        self._char_uuids = [bluetooth.UUID(u) for u in uuid_strs]

        self._tx_count = 0
        self._rx_count = 0
        self._tx_bytes = 0
        self._rx_bytes = 0

        self._retained = {}

        # Include both WRITE (0x0008) and WRITE_NO_RESPONSE (0x0004) so the
        # characteristic accepts both ATT Write Request and Write Command.
        # BLEClient.publish() uses Write Command (gattc_write mode=False) to
        # avoid EALREADY on rapid successive calls.
        default_flags = (self._FLAG_READ | self._FLAG_WRITE_NO_RESPONSE |
                         self._FLAG_WRITE | self._FLAG_NOTIFY)
        if char_flags is None:
            flags_list = [default_flags] * len(uuid_strs)
        else:
            if len(char_flags) != len(uuid_strs):
                raise ValueError("char_flags length must match char_uuids length")
            flags_list = list(char_flags)
        char_defs = tuple((u, f) for u, f in zip(self._char_uuids, flags_list))
        (handles_tuple,) = self._ble.gatts_register_services(
            ((self._service_uuid, char_defs),)
        )
        self._char_handles = list(handles_tuple)
        self._handle_to_idx = {h: i for i, h in enumerate(self._char_handles)}

        self._advertise()

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
    def connections(self) -> list:
        return list(self._connections.keys())

    @property
    def subscribed_topics(self) -> list:
        return list(self._subs)

    @property
    def dropped_event_count(self) -> int:
        return self._dropped_events

    @property
    def stats(self) -> dict:
        return {
            "tx_count": self._tx_count,
            "rx_count": self._rx_count,
            "tx_bytes": self._tx_bytes,
            "rx_bytes": self._rx_bytes,
        }

    @property
    def retained_topics(self) -> list:
        return list(self._retained.keys())

    def reset_stats(self) -> None:
        self._tx_count = 0
        self._rx_count = 0
        self._tx_bytes = 0
        self._rx_bytes = 0

    def get_connection_info(self, conn_handle: int = None) -> dict | list:
        def _format_addr(addr_bytes):
            if addr_bytes:
                return ":".join(f"{b:02X}" for b in addr_bytes)
            return "unknown"
        
        if conn_handle is not None:
            if conn_handle not in self._connections:
                return None
            return {
                "handle": conn_handle,
                "addr": _format_addr(self._connections.get(conn_handle))
            }
        
        return [
            {"handle": h, "addr": _format_addr(a)}
            for h, a in self._connections.items()
        ]

    def get_rssi(self, conn_handle: int = None) -> int | dict | None:
        if not self._connections:
            return None
        
        if conn_handle is not None:
            if conn_handle not in self._connections:
                return None
            try:
                return self._ble.gap_rssi(conn_handle)
            except Exception:
                return None
        
        result = {}
        for h in self._connections:
            try:
                result[h] = self._ble.gap_rssi(h)
            except Exception:
                result[h] = None
        return result

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
            
            for conn in list(self._connections.keys()):
                try:
                    self._ble.gap_disconnect(conn)
                except Exception:
                    pass
            
            self._connections.clear()
            self._queue.clear()
            self._subs.clear()
            self._retained.clear()
            self._ble.active(False)
        except Exception as e:
            self._error_callback("deinit_error", str(e))

    def _error_callback(self, error_type, details):
        if self._on_error:
            try:
                self._on_error(error_type, details)
            except Exception:
                pass
        else:
            print(f"[BLE] {error_type}: {details}")

    def _irq(self, event, data):
        if not self._active:
            return

        if event == self._IRQ_CENTRAL_CONNECT or event == self._IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            safe_data = (int(conn_handle), int(addr_type), bytes(addr))
        elif event == self._IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            safe_data = (int(conn_handle), int(attr_handle))
        else:
            return

        if len(self._queue) >= self._MAX_QUEUE:
            self._queue.pop(0)
            self._dropped_events += 1
            if self._dropped_events == 1 or self._dropped_events % 10 == 0:
                self._error_callback("queue_overflow", f"Dropped {self._dropped_events} events")

        self._queue.append((event, safe_data))
        if not self._in_dispatch:
            self._in_dispatch = True
            try:
                micropython.schedule(self._dispatch_cb, None)
            except RuntimeError:
                self._in_dispatch = False

    def _dispatch(self, _):
        while self._queue:
            try:
                event, data = self._queue.pop(0)
            except IndexError:
                break
            
            try:
                if event == self._IRQ_CENTRAL_CONNECT:
                    conn_handle, addr_type, addr = data
                    
                    if len(self._connections) >= self._max_connections:
                        self._error_callback("connection_limit", f"Rejecting connection (max {self._max_connections})")
                        try:
                            self._ble.gap_disconnect(conn_handle)
                        except Exception:
                            pass
                        continue
                    
                    self._connections[conn_handle] = bytes(addr)
                    if self._on_connect:
                        self._safe_call(self._on_connect, conn_handle)

                elif event == self._IRQ_CENTRAL_DISCONNECT:
                    conn_handle, _, _ = data
                    self._connections.pop(conn_handle, None)
                    if self._on_disconnect:
                        self._safe_call(self._on_disconnect, conn_handle)
                    
                    if self._active:
                        # Brief delay lets the BLE stack settle before re-advertising.
                        # Without this, a client that reconnects immediately may fail
                        # service discovery because the GATT server is still transitioning.
                        import time
                        time.sleep_ms(150)
                        self._advertise()

                elif event == self._IRQ_GATTS_WRITE:
                    conn_handle, attr_handle = data
                    if attr_handle in self._handle_to_idx:
                        char_idx = self._handle_to_idx[attr_handle]
                        try:
                            raw = self._ble.gatts_read(attr_handle)
                            self._rx_count += 1
                            self._rx_bytes += len(raw)
                            msg = raw.decode('utf-8', 'ignore').strip()
                            if msg:
                                self._handle_message(msg)
                        except Exception as e:
                            self._error_callback("decode_error", str(e))

            except Exception as e:
                self._error_callback("dispatch_error", str(e))

        self._in_dispatch = False
        if self._queue:
            self._in_dispatch = True
            try:
                micropython.schedule(self._dispatch_cb, None)
            except RuntimeError:
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
            
            for pattern in self._subs:
                if self._topic_matches(pattern, topic) and self._on_message:
                    self._safe_call(self._on_message, topic, payload)
                    break
        except Exception as e:
            self._error_callback("message_handler_error", str(e))

    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        if pattern == topic:
            return True
        
        if '#' not in pattern and '+' not in pattern:
            return False
        
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        pi = 0
        ti = 0
        
        while pi < len(pattern_parts):
            pp = pattern_parts[pi]
            
            if pp == '#':
                return pi == len(pattern_parts) - 1
            
            if ti >= len(topic_parts):
                return False
            
            if pp == '+':
                pi += 1
                ti += 1
            elif pp == topic_parts[ti]:
                pi += 1
                ti += 1
            else:
                return False
        
        return ti == len(topic_parts)

    def subscribe(self, topic: str) -> bool:
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")
        
        if ':' in topic:
            raise ValueError("Topic must not contain ':' character")
        
        if len(topic) > self._MAX_TOPIC_LENGTH:
            raise ValueError(f"Topic too long (max {self._MAX_TOPIC_LENGTH} chars)")
        
        parts = topic.split('/')
        for i, part in enumerate(parts):
            if '#' in part:
                if part != '#' or i != len(parts) - 1:
                    raise ValueError("# wildcard must be alone and at the end")
            if '+' in part and part != '+':
                raise ValueError("+ wildcard must be alone in its level")
        
        self._subs.add(topic)
        
        for rtopic, rmsg in self._retained.items():
            if self._topic_matches(topic, rtopic) and self._on_message:
                self._safe_call(self._on_message, rtopic, rmsg)
        
        if self._on_subscribe:
            self._safe_call(self._on_subscribe, topic)
        return True

    def unsubscribe(self, topic: str) -> bool:
        if topic in self._subs:
            self._subs.discard(topic)
            return True
        return False

    def publish(self, topic: str, message: str, *, char=0, retain: bool = False) -> int:
        if not isinstance(topic, str) or not topic:
            raise ValueError("Topic must be a non-empty string")
        
        if ':' in topic:
            raise ValueError("Topic must not contain ':' character")
        
        if '+' in topic or '#' in topic:
            raise ValueError("Wildcards not allowed in publish topic")
        
        if not isinstance(message, str):
            message = str(message)
        
        char_idx = self._resolve_char(char)
        char_handle = self._char_handles[char_idx]

        if retain:
            if message:
                self._retained[topic] = message
            else:
                self._retained.pop(topic, None) 
        
        try:
            frame = f"{topic}:{message}".encode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encode message: {e}")
        
        if len(frame) > self._MAX_MESSAGE_SIZE:
            raise ValueError(f"Message too large: {len(frame)} > {self._MAX_MESSAGE_SIZE} bytes")
        
        sent_count = 0
        failed_conns = []
        for conn in self._connections:
            try:
                self._ble.gatts_notify(conn, char_handle, frame)
                sent_count += 1
                self._tx_count += 1
                self._tx_bytes += len(frame)
            except Exception as e:
                failed_conns.append(conn)
                self._error_callback("notify_error", f"conn {conn}: {e}")
        
        for conn in failed_conns:
            self._connections.pop(conn, None)
        
        if self._on_publish:
            self._safe_call(self._on_publish, topic, message)
        
        return sent_count

    def _resolve_char(self, char) -> int:
        if char is None:
            return 0
        if isinstance(char, int):
            if 0 <= char < len(self._char_handles):
                return char
            raise ValueError(
                f"char index {char} out of range (0-{len(self._char_handles) - 1})"
            )
        if isinstance(char, str):
            target = bluetooth.UUID(char)
            for i, u in enumerate(self._char_uuids):
                if u == target:
                    return i
            raise ValueError(f"char UUID not registered: {char}")
        raise TypeError(f"char must be int, str, or None")

    def clear_retained(self, topic: str = None) -> int:
        if topic is not None:
            if topic in self._retained:
                del self._retained[topic]
                return 1
            return 0
        
        count = len(self._retained)
        self._retained.clear()
        return count

    def broadcast(self, data: bytes | str, interval_us: int = 100000) -> None:
        if not self._active:
            return
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if len(data) > 20:
            raise ValueError("Broadcast data too large (max 20 bytes)")
        
        try:
            adv_payload  = self._advertising_payload(manufacturer_data=data)
            resp_payload = self._advertising_payload(name=self._name, _flags=False)
            self._ble.gap_advertise(interval_us, adv_data=adv_payload, resp_data=resp_payload)
        except Exception as e:
            self._error_callback("broadcast_error", str(e))

    def stop_broadcast(self) -> None:
        self._advertise()

    def _safe_call(self, cb, *a):
        try:
            cb(*a)
        except Exception as e:
            self._error_callback("callback_error", str(e))

    def _advertise(self, interval_us=500000):
        if not self._active:
            return
        
        try:
            adv_payload  = self._advertising_payload(services=[self._service_uuid])
            resp_payload = self._advertising_payload(name=self._name, _flags=False)
            self._ble.gap_advertise(interval_us, adv_data=adv_payload, resp_data=resp_payload)
        except Exception as e:
            self._error_callback("advertise_error", str(e))

    @staticmethod
    def _advertising_payload(name=None, services=None, manufacturer_data=None, _flags=True):
        payload = bytearray()

        def _append(adv_type, value):
            if len(payload) + len(value) + 2 > 31:
                raise ValueError("advertising payload exceeds 31 bytes")
            payload.extend(struct.pack("BB", len(value) + 1, adv_type))
            payload.extend(value)

        if _flags:
            _append(0x01, struct.pack("B", 0x06))
        if name:
            _append(0x09, name.encode())
        if services:
            for uuid in services:
                b = bytes(uuid)
                _append(0x07 if len(b) == 16 else 0x03, b)
        if manufacturer_data:
            _append(0xFF, struct.pack("<H", 0xFFFF) + manufacturer_data)
        return payload

class BLEClient:
    _IRQ_SCAN_RESULT              = micropython.const(5)
    _IRQ_SCAN_DONE                = micropython.const(6)
    _IRQ_PERIPHERAL_CONNECT       = micropython.const(7)
    _IRQ_PERIPHERAL_DISCONNECT    = micropython.const(8)
    _IRQ_GATTC_SERVICE_RESULT     = micropython.const(9)
    _IRQ_GATTC_SERVICE_DONE       = micropython.const(10)
    _IRQ_GATTC_CHARACTERISTIC_RESULT = micropython.const(11)
    _IRQ_GATTC_CHARACTERISTIC_DONE   = micropython.const(12)
    _IRQ_GATTC_WRITE_DONE         = micropython.const(17)
    _IRQ_GATTC_NOTIFY             = micropython.const(18)

    _FLAG_WRITE                   = micropython.const(0x0008)
    _FLAG_NOTIFY                  = micropython.const(0x0010)

    _MAX_MESSAGE_SIZE             = micropython.const(512)
    _MAX_TOPIC_LENGTH             = micropython.const(64)

    def __init__(self, *,
                 service_uuid: str = "12345678-0000-0000-0000-000000000010",
                 char_uuid: str = "12345678-0000-0000-0000-000000000011",
                 char_uuids=None):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)

        self._service_uuid = bluetooth.UUID(service_uuid)

        uuid_strs = list(char_uuids) if char_uuids is not None else [char_uuid]
        if len(uuid_strs) == 0:
            raise ValueError("char_uuids must contain at least one UUID")
        self._char_uuids = [bluetooth.UUID(u) for u in uuid_strs]
        self._char_uuid_to_idx = {u: i for i, u in enumerate(self._char_uuids)}
        self._char_uuids_set = set(self._char_uuids)

        self._conn_handle = None
        self._char_handles = [None] * len(self._char_uuids)
        self._handle_to_idx = {}
        self._active = True

        self._scan_results = {}
        self._scanning = False
        self._scan_callback = None

        self._discovering = False
        self._service_start = None
        self._service_end = None
        self._pending_cccd = []
        self._pending_cccd_count = 0  # CCCD writes awaiting _IRQ_GATTC_WRITE_DONE
        self._service_not_found = False  # flag set when service discovery fails transiently

        self._subs = set()

        self._tx_count = 0
        self._rx_count = 0
        self._tx_bytes = 0
        self._rx_bytes = 0

        self._on_connect = None
        self._on_disconnect = None
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
    def is_connected(self) -> bool:
        return self._conn_handle is not None

    @property
    def subscribed_topics(self) -> list:
        return list(self._subs)

    @property
    def stats(self) -> dict:
        return {
            "tx_count": self._tx_count,
            "rx_count": self._rx_count,
            "tx_bytes": self._tx_bytes,
            "rx_bytes": self._rx_bytes,
        }

    def reset_stats(self) -> None:
        self._tx_count = 0
        self._rx_count = 0
        self._tx_bytes = 0
        self._rx_bytes = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.deinit()

    def deinit(self) -> None:
        if not self._active:
            return

        try:
            self._active = False
            if self._conn_handle is not None:
                try:
                    self._ble.gap_disconnect(self._conn_handle)
                except Exception:
                    pass
            self._conn_handle = None
            self._char_handles = [None] * len(self._char_uuids)
            self._handle_to_idx.clear()
            self._subs.clear()
            self._scan_results.clear()
            self._ble.active(False)
        except Exception as e:
            self._error_callback("deinit_error", str(e))

    def scan(self, duration_ms: int = 5000, callback: callable = None) -> list | None:
        if self._scanning:
            return None

        self._scan_results.clear()
        self._scanning = True
        self._scan_callback = callback

        try:
            self._ble.gap_scan(duration_ms, 30000, 30000, True)
        except Exception as e:
            self._scanning = False
            self._error_callback("scan_error", str(e))
            return None

        if callback is None:
            import time
            deadline = time.ticks_add(time.ticks_ms(), duration_ms + 500)
            while self._scanning and time.ticks_diff(deadline, time.ticks_ms()) > 0:
                time.sleep_ms(50)
            return self.scan_results

        return None

    def stop_scan(self) -> None:
        if self._scanning:
            try:
                self._ble.gap_scan(None)
            except Exception:
                pass
            self._scanning = False

    @property
    def scan_results(self) -> list:
        return [
            {"name": info["name"], "addr": addr, "rssi": info["rssi"]}
            for addr, info in self._scan_results.items()
        ]

    def connect(self, target: str, timeout_ms: int = 10000, retries: int = 2) -> bool:
        """Connect to a BLEServer by name or address.

        :param retries: How many extra attempts on transient service-discovery
            failures (e.g. server BLE stack not yet ready after a previous
            disconnect).  Each retry waits 300 ms before trying again.
        """
        if self._conn_handle is not None:
            self._error_callback("connect_error", "Already connected")
            return False

        addr_bytes = None
        addr_type = 0

        by_addr = None
        by_name = []
        for addr, info in self._scan_results.items():
            if addr == target:
                by_addr = info
                break
            if info["name"] == target:
                by_name.append(info)

        if by_addr is not None:
            addr_bytes = by_addr["addr_bytes"]
            addr_type = by_addr["addr_type"]
        elif by_name:
            if len(by_name) > 1:
                self._error_callback(
                    "connect_warning",
                    f"Multiple devices named '{target}' found ({len(by_name)}); selecting strongest RSSI"
                )
            selected = max(by_name, key=lambda item: item.get("rssi", -127))
            addr_bytes = selected["addr_bytes"]
            addr_type = selected["addr_type"]

        if addr_bytes is None:
            self._error_callback("connect_error", f"Device not found: {target}")
            return False

        import time
        for attempt in range(1 + retries):
            if attempt > 0:
                # Wait for the server's BLE stack to finish re-advertising
                # before retrying the connection.
                time.sleep_ms(300)
                self._error_callback(
                    "connect_retry",
                    f"Retrying connection to '{target}' (attempt {attempt + 1}/{1 + retries})"
                )

            self._service_not_found = False
            self._discovering = True
            try:
                self._ble.gap_connect(addr_type, addr_bytes)
            except Exception as e:
                self._discovering = False
                self._error_callback("connect_error", str(e))
                return False

            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            while self._discovering and time.ticks_diff(deadline, time.ticks_ms()) > 0:
                time.sleep_ms(50)

            success = self._conn_handle is not None and all(
                h is not None for h in self._char_handles
            )

            if success:
                return True

            # Ensure the connection is torn down before retrying.
            if self._conn_handle is not None:
                try:
                    self._ble.gap_disconnect(self._conn_handle)
                except Exception:
                    pass
                # Wait for _IRQ_PERIPHERAL_DISCONNECT to clear _conn_handle.
                disc_deadline = time.ticks_add(time.ticks_ms(), 500)
                while (self._conn_handle is not None and
                       time.ticks_diff(disc_deadline, time.ticks_ms()) > 0):
                    time.sleep_ms(20)

            # Only retry when the failure was a transient service-discovery miss.
            # Other failures (timeout, characteristic incomplete) are not retried.
            if not self._service_not_found:
                break

        return False

    def disconnect(self) -> None:
        if self._conn_handle is not None:
            try:
                self._ble.gap_disconnect(self._conn_handle)
            except Exception:
                pass

    def get_rssi(self) -> int | None:
        if self._conn_handle is None:
            return None
        try:
            return self._ble.gap_rssi(self._conn_handle)
        except Exception:
            return None

    def subscribe(self, topic: str) -> bool:
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")

        if ':' in topic:
            raise ValueError("Topic must not contain ':' character")

        if len(topic) > self._MAX_TOPIC_LENGTH:
            raise ValueError(f"Topic too long (max {self._MAX_TOPIC_LENGTH} chars)")

        parts = topic.split('/')
        for i, part in enumerate(parts):
            if '#' in part:
                if part != '#' or i != len(parts) - 1:
                    raise ValueError("# wildcard must be alone and at the end")
            if '+' in part and part != '+':
                raise ValueError("+ wildcard must be alone in its level")

        self._subs.add(topic)
        return True

    def unsubscribe(self, topic: str) -> bool:
        if topic in self._subs:
            self._subs.discard(topic)
            return True
        return False

    def publish(self, topic: str, message: str, *, char=0) -> bool:
        if self._conn_handle is None:
            self._error_callback("publish_error", "Not connected")
            return False

        if self._discovering:
            self._error_callback("publish_error", "Cannot publish during service discovery")
            return False

        char_idx = self._resolve_char(char)
        char_handle = self._char_handles[char_idx]
        if char_handle is None:
            self._error_callback("publish_error", f"Char {char_idx} not yet discovered")
            return False

        if not isinstance(topic, str) or not topic:
            raise ValueError("Topic must be a non-empty string")

        if ':' in topic:
            raise ValueError("Topic must not contain ':' character")

        if '+' in topic or '#' in topic:
            raise ValueError("Wildcards not allowed in publish topic")

        if not isinstance(message, str):
            message = str(message)

        try:
            frame = f"{topic}:{message}".encode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encode message: {e}")

        if len(frame) > self._MAX_MESSAGE_SIZE:
            raise ValueError(f"Message too large: {len(frame)} > {self._MAX_MESSAGE_SIZE} bytes")

        try:
            # mode=False: Write Command (no ATT response required).
            # Prevents EALREADY on rapid successive publishes (e.g. 100 ms interval).
            # BLEServer _IRQ_GATTS_WRITE fires for both Write Request and Write Command.
            self._ble.gattc_write(self._conn_handle, char_handle, frame, False)
            self._tx_count += 1
            self._tx_bytes += len(frame)
            return True
        except Exception as e:
            self._error_callback("publish_error", str(e))
            return False

    def _resolve_char(self, char) -> int:
        if char is None:
            return 0
        if isinstance(char, int):
            if 0 <= char < len(self._char_handles):
                return char
            raise ValueError(
                f"char index {char} out of range (0-{len(self._char_handles) - 1})"
            )
        if isinstance(char, str):
            target = bluetooth.UUID(char)
            for i, u in enumerate(self._char_uuids):
                if u == target:
                    return i
            raise ValueError(f"char UUID not registered: {char}")
        raise TypeError(f"char must be int, str, or None")

    def _error_callback(self, error_type, details):
        if self._on_error:
            try:
                self._on_error(error_type, details)
            except Exception:
                pass
        else:
            print(f"[BLEClient] {error_type}: {details}")

    def _irq(self, event, data):
        if not self._active:
            return

        if event == self._IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            addr_str = ":".join(f"{b:02X}" for b in bytes(addr))
            name = self._decode_name(adv_data)

            prev = self._scan_results.get(addr_str)
            if not name and prev and prev.get("name") and prev.get("name") != addr_str:
                name = prev["name"]

            self._scan_results[addr_str] = {
                "name": name or addr_str,
                "rssi": rssi,
                "addr_bytes": bytes(addr),
                "addr_type": addr_type,
            }

        elif event == self._IRQ_SCAN_DONE:
            self._scanning = False
            if self._scan_callback:
                try:
                    self._scan_callback(self.scan_results)
                except Exception:
                    pass

        elif event == self._IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._conn_handle = conn_handle
            self._service_start = None
            self._service_end = None
            self._char_handles = [None] * len(self._char_uuids)
            self._handle_to_idx.clear()
            self._pending_cccd = []
            self._pending_cccd_count = 0
            try:
                self._ble.gattc_discover_services(conn_handle, self._service_uuid)
            except Exception as e:
                self._error_callback("discovery_error", str(e))
                self._discovering = False

        elif event == self._IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, _, _ = data
            self._conn_handle = None
            self._char_handles = [None] * len(self._char_uuids)
            self._handle_to_idx.clear()
            self._discovering = False
            if self._on_disconnect:
                try:
                    self._on_disconnect()
                except Exception:
                    pass

        elif event == self._IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            if uuid == self._service_uuid:
                self._service_start = start_handle
                self._service_end = end_handle

        elif event == self._IRQ_GATTC_SERVICE_DONE:
            conn_handle, status = data
            if self._service_start is not None:
                start, end = self._service_start, self._service_end
                self._service_start = None
                self._service_end = None
                try:
                    self._ble.gattc_discover_characteristics(conn_handle, start, end)
                except Exception as e:
                    self._error_callback("discovery_error", str(e))
                    self._discovering = False
            else:
                self._error_callback(
                    "discovery_error",
                    f"Service not found: {self._service_uuid}"
                )
                self._service_not_found = True  # signal connect() to retry
                self._discovering = False
                if self._conn_handle is not None:
                    try:
                        self._ble.gap_disconnect(self._conn_handle)
                    except Exception:
                        pass

        elif event == self._IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            if uuid in self._char_uuids_set:
                idx = self._char_uuid_to_idx[uuid]
                self._char_handles[idx] = value_handle
                self._handle_to_idx[value_handle] = idx
                if properties & self._FLAG_NOTIFY:
                    self._pending_cccd.append((conn_handle, value_handle + 1))

        elif event == self._IRQ_GATTC_CHARACTERISTIC_DONE:
            self._pending_cccd_count = 0
            for conn_h, cccd_handle in self._pending_cccd:
                try:
                    self._ble.gattc_write(conn_h, cccd_handle, struct.pack('<H', 1), True)
                    self._pending_cccd_count += 1
                except Exception:
                    pass
            self._pending_cccd.clear()
            if self._pending_cccd_count == 0:
                self._discovering = False
                if all(h is not None for h in self._char_handles):
                    if self._on_connect:
                        try:
                            self._on_connect()
                        except Exception:
                            pass
                else:
                    self._error_callback(
                        "discovery_error",
                        "Characteristic discovery incomplete"
                    )
                    if self._conn_handle is not None:
                        try:
                            self._ble.gap_disconnect(self._conn_handle)
                        except Exception:
                            pass

        elif event == self._IRQ_GATTC_WRITE_DONE:
            if self._pending_cccd_count > 0:
                self._pending_cccd_count -= 1
                if self._pending_cccd_count == 0:
                    self._discovering = False
                    if all(h is not None for h in self._char_handles):
                        if self._on_connect:
                            try:
                                self._on_connect()
                            except Exception:
                                pass
                    else:
                        self._error_callback(
                            "discovery_error",
                            "Characteristic discovery incomplete"
                        )
                        if self._conn_handle is not None:
                            try:
                                self._ble.gap_disconnect(self._conn_handle)
                            except Exception:
                                pass

        elif event == self._IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            if value_handle in self._handle_to_idx:
                self._rx_count += 1
                self._rx_bytes += len(notify_data)
                self._handle_notify(bytes(notify_data))

    def _handle_notify(self, data: bytes):
        try:
            msg = data.decode('utf-8', 'ignore').strip()
            if not msg:
                return

            if ":" in msg:
                topic, payload = msg.split(":", 1)
            else:
                topic, payload = msg, ""

            if not topic:
                return

            for pattern in self._subs:
                if self._topic_matches(pattern, topic):
                    if self._on_message:
                        try:
                            self._on_message(topic, payload)
                        except Exception:
                            pass
                    break
            else:
                if not self._subs and self._on_message:
                    try:
                        self._on_message(topic, payload)
                    except Exception:
                        pass

        except Exception as e:
            self._error_callback("notify_error", str(e))

    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        if pattern == topic:
            return True

        if '#' not in pattern and '+' not in pattern:
            return False

        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')

        pi = 0
        ti = 0

        while pi < len(pattern_parts):
            pp = pattern_parts[pi]

            if pp == '#':
                return pi == len(pattern_parts) - 1

            if ti >= len(topic_parts):
                return False

            if pp == '+':
                pi += 1
                ti += 1
            elif pp == topic_parts[ti]:
                pi += 1
                ti += 1
            else:
                return False

        return ti == len(topic_parts)

    @staticmethod
    def _decode_name(adv_data) -> str | None:
        i = 0
        while i < len(adv_data):
            length = adv_data[i]
            if length == 0:
                break
            ad_type = adv_data[i + 1]
            if ad_type in (0x08, 0x09): 
                try:
                    return bytes(adv_data[i + 2:i + 1 + length]).decode('utf-8')
                except Exception:
                    pass
            i += 1 + length
        return None