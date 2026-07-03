"""
BLE Module

MQTT-style publish/subscribe messaging over Bluetooth Low Energy (BLE).
Provides a high-level interface for BLE communication with topic-based
messaging, wildcard subscriptions, and connection management.

Classes:

    - BLEBroker: Peripheral (GATT Server) - accepts connections, broadcasts
    - BLENode: Central (GATT Client) - scans, connects to BLEBroker

Key Features:

- MQTT-style topic-based messaging with wildcard support (+, #)
- Multiple simultaneous connections (up to 4 devices for BLEBroker)
- Transmission statistics and error tracking
- Retain messages for late subscribers (BLEBroker)
- Broadcast mode (beacon-style advertising)
- Connection information and RSSI monitoring
- Event callbacks for connection, message, and error handling

Protocol:
    Messages are formatted as "topic:payload" strings encoded in UTF-8.
    Maximum message size is 512 bytes.
    Both BLEBroker and BLENode use the same protocol for interoperability.

Author: PlanXLab Development Team
"""

from typing import Callable


class BLEBroker:
    """
    MQTT-style Pub/Sub BLE broker.
    
    Provides topic-based messaging over BLE with support for multiple
    connections, wildcard subscriptions, and message retention.
    
    Key Features:
    
        - Topic-based pub/sub messaging
        - MQTT-style wildcards: + (single level), # (multi level)
        - Up to 4 simultaneous connections
        - Retain messages for late subscribers
        - Broadcast mode (beacon advertising)
        - Statistics tracking (tx/rx counts and bytes)
    """
    
    def __init__(self, name: str = "BLEBroker", *,
                 service_uuid: str = "12345678-0000-0000-0000-000000000010",
                 char_uuid: str = "12345678-0000-0000-0000-000000000011",
                 max_connections: int = 4) -> None:
        """
        Initialize the BLE broker.
        
        :param name: Device name shown during BLE scanning (max 29 chars)
        :param service_uuid: Custom GATT service UUID
        :param char_uuid: Custom GATT characteristic UUID
        :param max_connections: Maximum simultaneous connections (1-4)
        
        :raises ValueError: If name too long or max_connections invalid
        
        Example
        --------
        ```python
            >>> from ticle import BLEBroker
            >>> broker = BLEBroker("MySensor")
            >>> broker.on_message = lambda t, m: print(f"{t}: {m}")
            >>> broker.subscribe("cmd/#")
        ```
        """
    
    def deinit(self) -> None:
        """
        Deinitialize the broker and release BLE resources.
        
        Disconnects all connected devices, stops advertising, and
        deactivates the BLE radio.
        
        Example
        --------
        ```python
            >>> broker.deinit()
        ```
        """
    
    def __enter__(self) -> "BLEBroker":
        """
        Context manager entry.
        
        Example
        --------
        ```python
            >>> with BLEBroker("Device") as broker:
            ...     broker.publish("status", "online")
        ```
        """
    
    def __exit__(self, *args) -> None:
        """
        Context manager exit. Calls deinit().
        """
    
    # ─────────────────────────────────────────────────────────────
    # Callback properties
    # ─────────────────────────────────────────────────────────────
    
    @property
    def on_connect(self) -> Callable[[int], None] | None:
        """
        Callback when a device connects.
        
        :return: Current callback or None
        
        Callback signature: ``callback(conn_handle: int) -> None``
        
        Example
        --------
        ```python
            >>> def handle_connect(handle):
            ...     print(f"Device connected: {handle}")
            >>> broker.on_connect = handle_connect
        ```
        """
    
    @on_connect.setter
    def on_connect(self, cb: Callable[[int], None] | None) -> None: ...
    
    @property
    def on_disconnect(self) -> Callable[[int], None] | None:
        """
        Callback when a device disconnects.
        
        :return: Current callback or None
        
        Callback signature: ``callback(conn_handle: int) -> None``
        
        Example
        --------
        ```python
            >>> broker.on_disconnect = lambda h: print(f"Disconnected: {h}")
        ```
        """
    
    @on_disconnect.setter
    def on_disconnect(self, cb: Callable[[int], None] | None) -> None: ...
    
    @property
    def on_message(self) -> Callable[[str, str], None] | None:
        """
        Callback when a message is received on a subscribed topic.
        
        :return: Current callback or None
        
        Callback signature: ``callback(topic: str, payload: str) -> None``
        
        Example
        --------
        ```python
            >>> def handle_message(topic, payload):
            ...     print(f"Received {topic}: {payload}")
            >>> broker.on_message = handle_message
        ```
        """
    
    @on_message.setter
    def on_message(self, cb: Callable[[str, str], None] | None) -> None: ...
    
    @property
    def on_publish(self) -> Callable[[str, str], None] | None:
        """
        Callback after a message is published.
        
        :return: Current callback or None
        
        Callback signature: ``callback(topic: str, message: str) -> None``
        """
    
    @on_publish.setter
    def on_publish(self, cb: Callable[[str, str], None] | None) -> None: ...
    
    @property
    def on_subscribe(self) -> Callable[[str], None] | None:
        """
        Callback when a topic is subscribed.
        
        :return: Current callback or None
        
        Callback signature: ``callback(topic: str) -> None``
        """
    
    @on_subscribe.setter
    def on_subscribe(self, cb: Callable[[str], None] | None) -> None: ...
    
    @property
    def on_error(self) -> Callable[[str, str], None] | None:
        """
        Callback when an error occurs.
        
        :return: Current callback or None
        
        Callback signature: ``callback(error_type: str, details: str) -> None``
        
        Error types: "queue_overflow", "connection_limit", "decode_error",
        "notify_error", "callback_error", etc.
        
        Example
        --------
        ```python
            >>> broker.on_error = lambda t, d: print(f"Error [{t}]: {d}")
        ```
        """
    
    @on_error.setter
    def on_error(self, cb: Callable[[str, str], None] | None) -> None: ...
    
    # ─────────────────────────────────────────────────────────────
    # Status properties
    # ─────────────────────────────────────────────────────────────
    
    @property
    def is_active(self) -> bool:
        """
        Check if broker is active and BLE radio is on.
        
        :return: True if active
        
        Example
        --------
        ```python
            >>> if broker.is_active:
            ...     broker.publish("status", "running")
        ```
        """
    
    @property
    def connection_count(self) -> int:
        """
        Number of currently connected devices.
        
        :return: Connection count (0-4)
        
        Example
        --------
        ```python
            >>> print(f"Connected devices: {broker.connection_count}")
        ```
        """
    
    @property
    def connections(self) -> list[int]:
        """
        List of connected device handles.
        
        :return: List of connection handle integers
        
        Example
        --------
        ```python
            >>> for handle in broker.connections:
            ...     info = broker.get_connection_info(handle)
            ...     print(f"Device {handle}: {info['addr']}")
        ```
        """
    
    @property
    def subscribed_topics(self) -> list[str]:
        """
        List of subscribed topic patterns.
        
        :return: List of topic pattern strings
        
        Example
        --------
        ```python
            >>> print(broker.subscribed_topics)
            ['sensor/+/temp', 'device/#']
        ```
        """
    
    @property
    def dropped_event_count(self) -> int:
        """
        Number of events dropped due to queue overflow.
        
        :return: Dropped event count
        """
    
    @property
    def stats(self) -> dict:
        """
        Transmission statistics.
        
        :return: Dict with tx_count, rx_count, tx_bytes, rx_bytes
        
        Example
        --------
        ```python
            >>> s = broker.stats
            >>> print(f"TX: {s['tx_count']} msgs, {s['tx_bytes']} bytes")
            >>> print(f"RX: {s['rx_count']} msgs, {s['rx_bytes']} bytes")
        ```
        """
    
    @property
    def retained_topics(self) -> list[str]:
        """
        List of topics with retained messages.
        
        :return: List of topic strings
        """
    
    def reset_stats(self) -> None:
        """
        Reset transmission statistics to zero.
        
        Example
        --------
        ```python
            >>> broker.reset_stats()
            >>> # ... do some work ...
            >>> print(broker.stats)
        ```
        """
    
    # ─────────────────────────────────────────────────────────────
    # Connection info
    # ─────────────────────────────────────────────────────────────
    
    def get_connection_info(self, conn_handle: int = None) -> dict | list | None:
        """
        Get connection information for device(s).
        
        :param conn_handle: Specific handle, or None for all connections
        :return: Dict with 'handle' and 'addr' for single connection,
                 list of dicts for all connections, or None if not found
        
        Example
        --------
        ```python
            >>> # Get all connections
            >>> for info in broker.get_connection_info():
            ...     print(f"Handle {info['handle']}: {info['addr']}")
            Handle 1: AA:BB:CC:DD:EE:FF
            
            >>> # Get specific connection
            >>> info = broker.get_connection_info(1)
            >>> print(info['addr'])
            'AA:BB:CC:DD:EE:FF'
        ```
        """
    
    def get_rssi(self, conn_handle: int = None) -> int | dict | None:
        """
        Get RSSI (signal strength) for connected device(s).
        
        :param conn_handle: Specific handle, or None for all connections
        :return: RSSI in dBm (-127 to 0) for single connection,
                 dict {handle: rssi} for all, or None if error
        
        Note: RSSI availability depends on platform support.
        
        Example
        --------
        ```python
            >>> rssi = broker.get_rssi(1)
            >>> if rssi:
            ...     print(f"Signal strength: {rssi} dBm")
            Signal strength: -45 dBm
            
            >>> # Get all RSSI values
            >>> all_rssi = broker.get_rssi()
            >>> for handle, rssi in all_rssi.items():
            ...     print(f"Device {handle}: {rssi} dBm")
        ```
        """
    
    # ─────────────────────────────────────────────────────────────
    # Pub/Sub API
    # ─────────────────────────────────────────────────────────────
    
    def subscribe(self, topic: str) -> bool:
        """
        Subscribe to a topic pattern.
        
        Supports MQTT-style wildcards:
            - ``+`` matches exactly one level (e.g., ``sensor/+/temp``)
            - ``#`` matches zero or more levels (e.g., ``device/#``)
        
        :param topic: Topic pattern to subscribe to
        :return: True on success
        
        :raises ValueError: If topic is empty, contains ':', is too long,
                           or has invalid wildcard usage
        
        Example
        --------
        ```python
            >>> # Exact topic
            >>> broker.subscribe("temperature")
            
            >>> # Single-level wildcard
            >>> broker.subscribe("sensor/+/value")  # matches sensor/1/value
            
            >>> # Multi-level wildcard
            >>> broker.subscribe("device/#")  # matches device/a/b/c
            
            >>> # Combined
            >>> broker.subscribe("home/+/sensor/#")
        ```
        """
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from a topic pattern.
        
        :param topic: Topic pattern to unsubscribe from
        :return: True if was subscribed, False otherwise
        
        Example
        --------
        ```python
            >>> broker.unsubscribe("sensor/+/temp")
            True
        ```
        """
    
    def publish(self, topic: str, message: str, *, retain: bool = False) -> int:
        """
        Publish a message to all connected devices.
        
        :param topic: Topic name (wildcards not allowed)
        :param message: Message payload (converted to string if needed)
        :param retain: If True, store message for future subscribers
        :return: Number of devices message was sent to
        
        :raises ValueError: If topic is empty, contains ':', contains wildcards,
                           or message is too large (>512 bytes)
        
        Example
        --------
        ```python
            >>> # Simple publish
            >>> broker.publish("sensor/temp", "23.5")
            2  # sent to 2 devices
            
            >>> # Publish with retain
            >>> broker.publish("status", "online", retain=True)
            
            >>> # Clear retained message (empty payload)
            >>> broker.publish("status", "", retain=True)
        ```
        """
    
    def clear_retained(self, topic: str = None) -> int:
        """
        Clear retained messages.
        
        :param topic: Specific topic to clear, or None for all
        :return: Number of cleared messages
        
        Example
        --------
        ```python
            >>> broker.clear_retained("status")  # clear one
            1
            >>> broker.clear_retained()  # clear all
            3
        ```
        """
    
    # ─────────────────────────────────────────────────────────────
    # Broadcast mode
    # ─────────────────────────────────────────────────────────────
    
    def broadcast(self, data: bytes | str, interval_us: int = 100000) -> None:
        """
        Broadcast data via advertising (beacon mode).
        
        This allows sending data without requiring a connection.
        Data is included in the advertising packet as manufacturer data.
        
        :param data: Data to broadcast (max 20 bytes for compatibility)
        :param interval_us: Advertising interval in microseconds
        
        :raises ValueError: If data exceeds 20 bytes
        
        Example
        --------
        ```python
            >>> # Broadcast sensor reading
            >>> broker.broadcast(b"TEMP:23.5")
            
            >>> # String is auto-encoded to UTF-8
            >>> broker.broadcast("HELLO", interval_us=50000)
        ```
        """
    
    def stop_broadcast(self) -> None:
        """
        Stop broadcasting and resume normal advertising.
        
        Example
        --------
        ```python
            >>> broker.broadcast(b"BEACON")
            >>> # ... later ...
            >>> broker.stop_broadcast()
        ```
        """


class BLENode:
    """
    BLE Central (GATT Client) for connecting to BLEBroker.
    
    Scans for and connects to BLEBroker devices, enabling bidirectional
    pub/sub messaging. This is the client-side complement to BLEBroker.
    
    Key Features:
    
        - Device scanning with name/address filtering
        - Connection management with timeout support
        - Topic-based messaging (same protocol as BLEBroker)
        - MQTT-style wildcard subscriptions for received messages
        - Statistics tracking (tx/rx counts and bytes)
    
    Example
    --------
    Basic usage pattern::
    
        >>> from ble import BLENode
        >>> 
        >>> node = BLENode()
        >>> 
        >>> # Set up callbacks
        >>> node.on_connect = lambda: print("Connected!")
        >>> node.on_message = lambda t, p: print(f"{t}: {p}")
        >>> node.on_disconnect = lambda: print("Disconnected!")
        >>> 
        >>> # Scan for devices
        >>> devices = node.scan(duration_ms=3000)
        >>> print(devices)
        >>> 
        >>> # Connect to a BLEBroker
        >>> if node.connect("BLEBroker"):
        ...     node.subscribe("sensor/#")
        ...     node.publish("cmd", "start")
    """
    
    def __init__(self, *,
                 service_uuid: str = "12345678-0000-0000-0000-000000000010",
                 char_uuid: str = "12345678-0000-0000-0000-000000000011"):
        """
        Initialize BLENode in central mode.
        
        :param service_uuid: Service UUID to discover (must match BLEBroker)
        :param char_uuid: Characteristic UUID for messaging (must match BLEBroker)
        
        Example
        --------
        ```python
            >>> # Default UUIDs (compatible with default BLEBroker)
            >>> node = BLENode()
            
            >>> # Custom UUIDs (must match your BLEBroker configuration)
            >>> node = BLENode(
            ...     service_uuid="AAAAAAAA-0000-0000-0000-000000000010",
            ...     char_uuid="AAAAAAAA-0000-0000-0000-000000000011"
            ... )
        ```
        """
    
    # ─────────────────────────────────────────────────────────────
    # Callback properties
    # ─────────────────────────────────────────────────────────────
    
    @property
    def on_connect(self) -> Callable[[], None] | None:
        """
        Callback invoked when successfully connected to a BLEBroker.
        
        Signature: ``callback() -> None``
        
        Example
        --------
        ```python
            >>> def handle_connect():
            ...     print("Connected!")
            ...     node.subscribe("sensor/#")
            >>> node.on_connect = handle_connect
        ```
        """
    
    @on_connect.setter
    def on_connect(self, cb: Callable[[], None] | None) -> None: ...
    
    @property
    def on_disconnect(self) -> Callable[[], None] | None:
        """
        Callback invoked when disconnected from BLEBroker.
        
        Signature: ``callback() -> None``
        
        Example
        --------
        ```python
            >>> def handle_disconnect():
            ...     print("Disconnected! Attempting reconnect...")
            ...     node.connect("BLEBroker")
            >>> node.on_disconnect = handle_disconnect
        ```
        """
    
    @on_disconnect.setter
    def on_disconnect(self, cb: Callable[[], None] | None) -> None: ...
    
    @property
    def on_message(self) -> Callable[[str, str], None] | None:
        """
        Callback invoked when a message is received from BLEBroker.
        
        Messages are filtered based on subscriptions with wildcard matching.
        If no subscriptions are set, all messages are delivered.
        
        Signature: ``callback(topic: str, payload: str) -> None``
        
        :param topic: The message topic
        :param payload: The message payload
        
        Example
        --------
        ```python
            >>> def handle_message(topic, payload):
            ...     print(f"Received {topic}: {payload}")
            ...     if topic == "cmd/response":
            ...         process_response(payload)
            >>> node.on_message = handle_message
        ```
        """
    
    @on_message.setter
    def on_message(self, cb: Callable[[str, str], None] | None) -> None: ...
    
    @property
    def on_error(self) -> Callable[[str, str], None] | None:
        """
        Callback invoked when an error occurs.
        
        Signature: ``callback(error_type: str, details: str) -> None``
        
        Error types include:
            - ``scan_error``: Scanning failed
            - ``connect_error``: Connection failed
            - ``discovery_error``: Service discovery failed
            - ``publish_error``: Message transmission failed
            - ``notify_error``: Notification handling failed
            - ``deinit_error``: Cleanup failed
        
        Example
        --------
        ```python
            >>> def handle_error(err_type, details):
            ...     print(f"Error [{err_type}]: {details}")
            ...     if err_type == "connect_error":
            ...         node.scan()  # Rescan devices
            >>> node.on_error = handle_error
        ```
        """
    
    @on_error.setter
    def on_error(self, cb: Callable[[str, str], None] | None) -> None: ...
    
    # ─────────────────────────────────────────────────────────────
    # Status properties
    # ─────────────────────────────────────────────────────────────
    
    @property
    def is_active(self) -> bool:
        """
        Check if BLE is active.
        
        :return: True if BLE adapter is active, False otherwise
        
        Example
        --------
        ```python
            >>> if node.is_active:
            ...     node.scan()
        ```
        """
    
    @property
    def is_connected(self) -> bool:
        """
        Check if connected to a BLEBroker.
        
        :return: True if connected, False otherwise
        
        Example
        --------
        ```python
            >>> if node.is_connected:
            ...     node.publish("status", "online")
        ```
        """
    
    @property
    def subscribed_topics(self) -> list[str]:
        """
        Get list of currently subscribed topics.
        
        :return: List of topic patterns including wildcards
        
        Example
        --------
        ```python
            >>> node.subscribe("sensor/+")
            >>> node.subscribe("cmd/#")
            >>> print(node.subscribed_topics)
            ['sensor/+', 'cmd/#']
        ```
        """
    
    @property
    def stats(self) -> dict[str, int]:
        """
        Get transmission statistics.
        
        :return: Dictionary with keys:
            - ``tx_count``: Number of messages sent
            - ``rx_count``: Number of messages received
            - ``tx_bytes``: Total bytes sent
            - ``rx_bytes``: Total bytes received
        
        Example
        --------
        ```python
            >>> stats = node.stats
            >>> print(f"Sent: {stats['tx_count']} msgs, {stats['tx_bytes']} bytes")
            >>> print(f"Recv: {stats['rx_count']} msgs, {stats['rx_bytes']} bytes")
        ```
        """
    
    def reset_stats(self) -> None:
        """
        Reset all transmission statistics to zero.
        
        Example
        --------
        ```python
            >>> node.reset_stats()
            >>> # ... perform operations ...
            >>> print(node.stats)  # Fresh statistics
        ```
        """
    
    @property
    def scan_results(self) -> list[dict]:
        """
        Get results from the last scan operation.
        
        :return: List of discovered devices, each with:
            - ``name``: Device name (or address if no name)
            - ``addr``: MAC address string (XX:XX:XX:XX:XX:XX)
            - ``rssi``: Signal strength in dBm
        
        Example
        --------
        ```python
            >>> node.scan(duration_ms=3000)
            >>> for dev in node.scan_results:
            ...     print(f"{dev['name']} ({dev['addr']}): {dev['rssi']} dBm")
            BLEBroker (A4:C1:38:00:11:22): -45 dBm
            OtherDevice (B8:27:EB:AA:BB:CC): -72 dBm
        ```
        """
    
    # ─────────────────────────────────────────────────────────────
    # Context manager
    # ─────────────────────────────────────────────────────────────
    
    def __enter__(self) -> "BLENode":
        """Enter context manager."""
    
    def __exit__(self, *args) -> None:
        """Exit context manager, calls deinit()."""
    
    def deinit(self) -> None:
        """
        Clean up BLE resources.
        
        Disconnects from any connected device, clears all subscriptions,
        and deactivates the BLE adapter.
        
        Example
        --------
        ```python
            >>> node = BLENode()
            >>> try:
            ...     node.connect("BLEBroker")
            ...     # ... operations ...
            ... finally:
            ...     node.deinit()
            
            >>> # Or use context manager
            >>> with BLENode() as node:
            ...     node.connect("BLEBroker")
        ```
        """
    
    # ─────────────────────────────────────────────────────────────
    # Scanning
    # ─────────────────────────────────────────────────────────────
    
    def scan(self, duration_ms: int = 5000, 
             callback: Callable[[list[dict]], None] | None = None) -> list[dict] | None:
        """
        Scan for nearby BLE devices.
        
        Can operate in blocking mode (returns results) or async mode 
        (invokes callback when complete).
        
        :param duration_ms: Scan duration in milliseconds (default 5000)
        :param callback: Optional callback for async mode. If provided,
            returns immediately and invokes callback(results) when done.
        
        :return: List of discovered devices in blocking mode, None in async mode
        
        Example
        --------
        ```python
            >>> # Blocking mode
            >>> devices = node.scan(duration_ms=3000)
            >>> for dev in devices:
            ...     print(f"{dev['name']}: {dev['rssi']} dBm")
            
            >>> # Async mode
            >>> def on_scan_done(results):
            ...     print(f"Found {len(results)} devices")
            ...     for dev in results:
            ...         if "Broker" in dev['name']:
            ...             node.connect(dev['name'])
            >>> node.scan(duration_ms=5000, callback=on_scan_done)
        ```
        """
    
    def stop_scan(self) -> None:
        """
        Stop an ongoing scan operation.
        
        Example
        --------
        ```python
            >>> # Start async scan
            >>> node.scan(duration_ms=10000, callback=handle_results)
            >>> 
            >>> # Stop early if device found
            >>> for dev in node.scan_results:
            ...     if dev['name'] == "BLEBroker":
            ...         node.stop_scan()
            ...         break
        ```
        """
    
    # ─────────────────────────────────────────────────────────────
    # Connection
    # ─────────────────────────────────────────────────────────────
    
    def connect(self, target: str, timeout_ms: int = 10000) -> bool:
        """
        Connect to a BLEBroker device.
        
        The target device must have been discovered in a previous scan.
        Connection includes automatic service and characteristic discovery.
        
        :param target: Device name or MAC address from scan results
        :param timeout_ms: Connection timeout in milliseconds (default 10000)
        
        :return: True if connected and ready, False otherwise
        
        Example
        --------
        ```python
            >>> # Connect by name
            >>> node.scan()
            >>> if node.connect("BLEBroker"):
            ...     print("Connected!")
            ...     node.publish("status", "online")
            
            >>> # Connect by address
            >>> if node.connect("A4:C1:38:00:11:22"):
            ...     print("Connected by address!")
            
            >>> # With timeout
            >>> if node.connect("BLEBroker", timeout_ms=5000):
            ...     print("Quick connect succeeded!")
        ```
        """
    
    def disconnect(self) -> None:
        """
        Disconnect from the current BLEBroker.
        
        Triggers the on_disconnect callback if set.
        
        Example
        --------
        ```python
            >>> if node.is_connected:
            ...     node.publish("status", "offline")
            ...     node.disconnect()
        ```
        """
    
    def get_rssi(self) -> int | None:
        """
        Get current connection RSSI (signal strength).
        
        :return: RSSI in dBm if connected, None otherwise
        
        Example
        --------
        ```python
            >>> rssi = node.get_rssi()
            >>> if rssi is not None:
            ...     if rssi < -80:
            ...         print("Weak signal!")
            ...     print(f"Signal strength: {rssi} dBm")
        ```
        """
    
    # ─────────────────────────────────────────────────────────────
    # Pub/Sub API
    # ─────────────────────────────────────────────────────────────
    
    def subscribe(self, topic: str) -> bool:
        """
        Subscribe to a topic pattern for local message filtering.
        
        Subscriptions filter messages received from the BLEBroker.
        Supports MQTT-style wildcards:
        
            - ``+`` : Matches exactly one level (sensor/+/temp)
            - ``#`` : Matches zero or more levels, must be last (sensor/#)
        
        Note: This is local filtering only. The BLEBroker sends all messages
        to connected devices; this method filters which ones trigger on_message.
        
        :param topic: Topic pattern to subscribe to
        
        :return: True if subscription added
        
        :raises ValueError: If topic is invalid or contains wildcards incorrectly
        
        Example
        --------
        ```python
            >>> # Exact topic
            >>> node.subscribe("sensor/temperature")
            
            >>> # Single-level wildcard
            >>> node.subscribe("sensor/+/value")  # Matches sensor/temp/value, sensor/humidity/value
            
            >>> # Multi-level wildcard
            >>> node.subscribe("device/#")  # Matches device, device/status, device/a/b/c
        ```
        """
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Remove a topic subscription.
        
        :param topic: Exact topic pattern to unsubscribe from
        
        :return: True if removed, False if not subscribed
        
        Example
        --------
        ```python
            >>> node.subscribe("sensor/#")
            >>> # ... later ...
            >>> node.unsubscribe("sensor/#")
        ```
        """
    
    def publish(self, topic: str, message: str) -> bool:
        """
        Publish a message to the connected BLEBroker.
        
        The message is sent as "topic:payload" format to the BLEBroker,
        which can then distribute it to other connected devices or process
        it locally.
        
        :param topic: Topic name (no wildcards allowed)
        :param message: Message payload (will be converted to string)
        
        :return: True if sent successfully, False otherwise
        
        :raises ValueError: If topic is invalid, contains wildcards, or
            message is too large (>512 bytes after encoding)
        
        Example
        --------
        ```python
            >>> # Send a command
            >>> node.publish("cmd", "start")
            
            >>> # Send sensor data
            >>> node.publish("sensor/temperature", "23.5")
            
            >>> # Send JSON payload
            >>> import json
            >>> node.publish("data", json.dumps({"temp": 23.5, "humidity": 65}))
        ```
        """