import bluetooth
import micropython
import ustruct

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


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
