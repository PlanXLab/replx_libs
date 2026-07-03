# @package: mesh
# @version: 1.0.0
# @type: core
# @category: communication
# @interface: BLE
# @depends: none
# @platforms: rp2, esp32, nrf
# @tags: mesh, ble, bluetooth, network, multi-hop
# @author: PlanXLab Development Team

import bluetooth
import struct
import time
from micropython import const

class BLEMesh:    
    _ADV_TYPE_MANUFACTURER = const(0xFF)
    _COMPANY_ID = const(0xFFFF)  # Reserved for internal use
    
    _MSG_TYPE_DATA     = const(0x01)
    _MSG_TYPE_PING     = const(0x02)
    _MSG_TYPE_PONG     = const(0x03)
    
    _DEFAULT_TTL       = const(3)
    _MAX_TTL           = const(7)
    _MAX_PAYLOAD_SIZE  = const(20)  # BLE advertising limit
    _SEEN_CACHE_SIZE   = const(32)
    
    _SCAN_INTERVAL_US  = const(30000)
    _SCAN_WINDOW_US    = const(30000)
    _ADV_INTERVAL_US   = const(100000)
    
    def __init__(self, node_id: int = None, *, group_id: int = 0x01):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        
        # Node identification
        if node_id is None:
            # Use last 2 bytes of MAC address
            mac = self._ble.config('mac')[1]
            node_id = (mac[4] << 8) | mac[5]
        
        self._node_id = node_id & 0xFFFF
        self._group_id = group_id & 0xFF
        self._seq = 0
        
        # Message deduplication cache (circular buffer)
        self._seen = [0] * self._SEEN_CACHE_SIZE
        self._seen_idx = 0
        
        # State
        self._active = True
        self._running = False
        self._relay_enabled = True
        
        # Statistics
        self._tx_count = 0
        self._rx_count = 0
        self._relay_count = 0
        self._dup_count = 0
        
        # Callbacks
        self._on_message = None
        self._on_ping = None
        self._on_error = None
        
        # Pending transmissions (for delayed relay)
        self._pending_relay = []

    @property
    def node_id(self) -> int:
        return self._node_id
    
    @property
    def group_id(self) -> int:
        return self._group_id
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def relay_enabled(self) -> bool:
        return self._relay_enabled
    
    @relay_enabled.setter
    def relay_enabled(self, value: bool):
        self._relay_enabled = bool(value)

    @property
    def stats(self) -> dict:
        return {
            "tx_count": self._tx_count,
            "rx_count": self._rx_count,
            "relay_count": self._relay_count,
            "dup_count": self._dup_count,
        }
    
    def reset_stats(self) -> None:
        self._tx_count = 0
        self._rx_count = 0
        self._relay_count = 0
        self._dup_count = 0

    @property
    def on_message(self):
        return self._on_message
    
    @on_message.setter
    def on_message(self, cb):
        self._on_message = cb

    @property
    def on_ping(self):
        return self._on_ping
    
    @on_ping.setter
    def on_ping(self, cb):
        self._on_ping = cb

    @property
    def on_error(self):
        return self._on_error
    
    @on_error.setter
    def on_error(self, cb):
        self._on_error = cb

    def start(self) -> bool:
        if self._running:
            return True
        
        if not self._active:
            return False
        
        try:
            # Start scanning for mesh messages
            self._ble.gap_scan(0, self._SCAN_INTERVAL_US, self._SCAN_WINDOW_US, True)
            self._running = True
            return True
        except Exception as e:
            self._error_callback("start_error", str(e))
            return False
    
    def stop(self) -> None:
        if not self._running:
            return
        
        try:
            self._ble.gap_scan(None)
        except Exception:
            pass
        
        self._running = False
        self._pending_relay.clear()
    
    def deinit(self) -> None:
        self.stop()
        self._active = False
        try:
            self._ble.active(False)
        except Exception:
            pass

    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.deinit()

    def send(self, data: bytes | str, *, ttl: int = None, target_group: int = None) -> bool:
        if not self._running:
            return False
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if len(data) > self._MAX_PAYLOAD_SIZE - 8:  # Header size
            raise ValueError(f"Payload too large (max {self._MAX_PAYLOAD_SIZE - 8} bytes)")
        
        if ttl is None:
            ttl = self._DEFAULT_TTL
        ttl = min(ttl, self._MAX_TTL)
        
        if target_group is None:
            target_group = self._group_id
        
        return self._broadcast(self._MSG_TYPE_DATA, data, ttl, target_group)
    
    def ping(self, target_node: int = 0xFFFF) -> bool:
        if not self._running:
            return False
        
        # Payload: target node ID (0xFFFF = broadcast ping)
        payload = struct.pack('<H', target_node)
        return self._broadcast(self._MSG_TYPE_PING, payload, self._DEFAULT_TTL, self._group_id)
    
    def _broadcast(self, msg_type: int, payload: bytes, ttl: int, group: int) -> bool:
        self._seq = (self._seq + 1) & 0xFF
        
        # Mark as seen to prevent self-relay
        msg_hash = self._hash_message(self._node_id, self._seq)
        self._mark_seen(msg_hash)
        
        # Build packet
        packet = self._build_packet(msg_type, self._node_id, self._seq, ttl, group, payload)
        
        try:
            self._advertise(packet)
            self._tx_count += 1
            return True
        except Exception as e:
            self._error_callback("send_error", str(e))
            return False

    def _advertise(self, packet: bytes, interval_us: int = None) -> None:
        if interval_us is None:
            interval_us = self._ADV_INTERVAL_US
        
        # Build advertising payload with manufacturer data
        adv_data = bytearray()
        adv_data.append(len(packet) + 3)  # Length
        adv_data.append(self._ADV_TYPE_MANUFACTURER)
        adv_data.extend(struct.pack('<H', self._COMPANY_ID))
        adv_data.extend(packet)
        
        # Brief advertising burst
        self._ble.gap_advertise(interval_us, adv_data=bytes(adv_data), connectable=False)
        time.sleep_ms(50)  # Advertise for 50ms
        self._ble.gap_advertise(None)  # Stop advertising

    def _build_packet(self, msg_type: int, src: int, seq: int, ttl: int, group: int, payload: bytes) -> bytes:
        header = struct.pack('<BHBBBB', msg_type, src, seq, ttl, group, len(payload))
        return header + payload
    
    def _parse_packet(self, data: bytes) -> dict | None:
        if len(data) < 7:
            return None
        
        msg_type, src, seq, ttl, group, payload_len = struct.unpack('<BHBBBB', data[:7])
        
        if len(data) < 7 + payload_len:
            return None
        
        return {
            'type': msg_type,
            'src': src,
            'seq': seq,
            'ttl': ttl,
            'group': group,
            'payload': data[7:7 + payload_len],
        }

    def _irq(self, event, data):
        if not self._active or not self._running:
            return
        
        _IRQ_SCAN_RESULT = 5
        
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            self._process_adv(bytes(adv_data), rssi)

    def _process_adv(self, adv_data: bytes, rssi: int):
        # Parse advertising data to find manufacturer data
        i = 0
        while i < len(adv_data):
            length = adv_data[i]
            if length == 0:
                break
            
            if i + length >= len(adv_data):
                break
            
            ad_type = adv_data[i + 1]
            
            if ad_type == self._ADV_TYPE_MANUFACTURER and length >= 4:
                # Check company ID
                company_id = struct.unpack('<H', adv_data[i + 2:i + 4])[0]
                if company_id == self._COMPANY_ID:
                    # Extract mesh packet
                    packet = adv_data[i + 4:i + 1 + length]
                    self._handle_packet(packet, rssi)
                    return
            
            i += 1 + length

    def _handle_packet(self, packet: bytes, rssi: int):
        msg = self._parse_packet(packet)
        if msg is None:
            return
        
        # Ignore own messages
        if msg['src'] == self._node_id:
            return
        
        # Check group (0x00 = all groups, or specific group)
        if msg['group'] != 0x00 and msg['group'] != self._group_id:
            return
        
        # Deduplication check
        msg_hash = self._hash_message(msg['src'], msg['seq'])
        if self._is_seen(msg_hash):
            self._dup_count += 1
            return
        
        self._mark_seen(msg_hash)
        self._rx_count += 1
        
        # Handle by message type
        if msg['type'] == self._MSG_TYPE_DATA:
            self._handle_data(msg, rssi)
        elif msg['type'] == self._MSG_TYPE_PING:
            self._handle_ping(msg, rssi)
        elif msg['type'] == self._MSG_TYPE_PONG:
            self._handle_pong(msg, rssi)
        
        # Relay if TTL > 0 and relay enabled
        if self._relay_enabled and msg['ttl'] > 0:
            self._relay_message(msg)

    def _handle_data(self, msg: dict, rssi: int):
        if self._on_message:
            try:
                self._on_message(msg['src'], msg['payload'], rssi)
            except Exception:
                pass

    def _handle_ping(self, msg: dict, rssi: int):
        target = struct.unpack('<H', msg['payload'][:2])[0] if len(msg['payload']) >= 2 else 0xFFFF
        
        # Respond if ping is for us or broadcast
        if target == 0xFFFF or target == self._node_id:
            # Send pong with our node ID and received RSSI
            pong_payload = struct.pack('<HBb', msg['src'], msg['seq'], rssi)
            self._broadcast(self._MSG_TYPE_PONG, pong_payload, self._DEFAULT_TTL, self._group_id)
            
            if self._on_ping:
                try:
                    self._on_ping(msg['src'], rssi)
                except Exception:
                    pass

    def _handle_pong(self, msg: dict, rssi: int):
        if len(msg['payload']) >= 4:
            target, ping_seq, reported_rssi = struct.unpack('<HBb', msg['payload'][:4])
            if target == self._node_id and self._on_ping:
                try:
                    self._on_ping(msg['src'], reported_rssi)
                except Exception:
                    pass

    def _relay_message(self, msg: dict):
        # Decrease TTL and forward
        new_ttl = msg['ttl'] - 1
        packet = self._build_packet(
            msg['type'], msg['src'], msg['seq'],
            new_ttl, msg['group'], msg['payload']
        )
        
        try:
            # Small random delay to reduce collisions
            time.sleep_ms(10 + (self._node_id & 0x1F))
            self._advertise(packet)
            self._relay_count += 1
        except Exception as e:
            self._error_callback("relay_error", str(e))

    @staticmethod
    def _hash_message(src: int, seq: int) -> int:
        return ((src & 0xFFFF) << 8) | (seq & 0xFF)
    
    def _is_seen(self, msg_hash: int) -> bool:
        return msg_hash in self._seen
    
    def _mark_seen(self, msg_hash: int):
        self._seen[self._seen_idx] = msg_hash
        self._seen_idx = (self._seen_idx + 1) % self._SEEN_CACHE_SIZE

    def _error_callback(self, error_type: str, details: str):
        if self._on_error:
            try:
                self._on_error(error_type, details)
            except Exception:
                pass
        else:
            print(f"[BLEMesh] {error_type}: {details}")
