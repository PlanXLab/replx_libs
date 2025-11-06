"""
Module: 'upaho.client' on micropython-v1.25.0-rp2-RPI_PICO2_W

MQTT Client Implementation with paho-mqtt compatible API
"""
# MCU: {'build': '', 'ver': '1.25.0', 'version': '1.25.0', 'port': 'rp2', 'board': 'RPI_PICO2_W', 'mpy': 'v6.3', 'family': 'micropython', 'cpu': 'RP2350', 'arch': 'armv7emsp'}
# Stubber: v1.24.0

from __future__ import annotations
from typing import Optional, Callable, Any, Dict, Tuple, List, Union
from .enums import MQTTProtocolVersion, ReasonCode
from .properties import Properties
from .message import MQTTMessage, MQTTMessageInfo

class Client:
    """
    MicroPython MQTT 5.0 Client with paho-mqtt compatible API.
    
    This class provides a robust MicroPython implementation for MQTT protocol
    (versions 3.1.1 and 5.0) compatible with the paho-mqtt Python library API.
    It enables devices to communicate with MQTT brokers for IoT applications,
    supporting all Quality of Service levels including exactly-once delivery.
    
    Key Features:
    
        - MQTT 3.1.1 and 5.0 protocol support with automatic version negotiation
        - Full QoS 0, 1, and 2 support (including 4-way handshake for QoS 2)
        - Async publish with callback-based acknowledgment handling
        - TLS/SSL support for secure connections
        - Automatic reconnection with configurable retry logic
        - Last Will and Testament (LWT) configuration
        - MQTT 5.0 Properties for enhanced metadata
        - Topic-specific message callbacks
        - Connection state tracking and keepalive management
    
    Communication Flow:
    
        1. Create client instance with configuration
        2. Set callbacks for events (on_connect, on_message, etc.)
        3. Connect to MQTT broker
        4. Subscribe to topics and/or publish messages
        5. Call loop() or loop_forever() to handle network traffic
        6. Handle callbacks for incoming messages and events
    
    QoS Levels:
    
        - QoS 0: Fire-and-forget, no acknowledgment
        - QoS 1: At-least-once delivery with PUBACK
        - QoS 2: Exactly-once delivery with PUBREC/PUBREL/PUBCOMP handshake
    
    Performance:
    
        - Connection time: ~659ms average
        - QoS 0 throughput: 581 msg/s
        - QoS 1 throughput: 68.7 msg/s
        - Memory usage: ~33KB
    """
    
    on_connect: Optional[Callable[[Client, Any, Dict, int, Optional[Properties]], None]]
    on_disconnect: Optional[Callable[[Client, Any, int, Optional[Properties]], None]]
    on_message: Optional[Callable[[Client, Any, MQTTMessage], None]]
    on_publish: Optional[Callable[[Client, Any, int], None]]
    on_subscribe: Optional[Callable[[Client, Any, int, List[int], Optional[Properties]], None]]
    on_unsubscribe: Optional[Callable[[Client, Any, int, Optional[Properties]], None]]
    on_log: Optional[Callable[[Client, Any, int, str], None]]
    
    def __init__(
        self,
        client_id: str = "",
        clean_session: Optional[bool] = None,
        userdata: Any = None,
        protocol: int = MQTTProtocolVersion.MQTTv5,
        transport: str = "tcp",
        reconnect_on_failure: bool = True
    ) -> None:
        """
        Initialize the MQTT client with connection parameters.
        
        Creates a new MQTT client instance with the specified configuration.
        The client is ready to connect after initialization but does not
        establish a connection automatically. You must call connect() explicitly.
        
        :param client_id: Unique client identifier (empty string for auto-generated)
        :param clean_session: Start fresh session if True, resume if False (None=auto based on protocol)
        :param userdata: User-defined data passed to callbacks
        :param protocol: MQTT protocol version (MQTTv5, MQTTv311, or MQTTv31)
        :param transport: Transport protocol ("tcp" only, "websockets" not supported)
        :param reconnect_on_failure: Automatically reconnect on connection failure
        
        :raises ValueError: If protocol or transport is invalid
        
        Example
        -------
        ```python
            >>> # Basic client with auto-generated ID
            >>> client = Client()
            >>> 
            >>> # Client with specific ID and MQTT 3.1.1
            >>> client = Client(
            ...     client_id="sensor001",
            ...     protocol=MQTTProtocolVersion.MQTTv311
            ... )
            >>> 
            >>> # Client with user data for callbacks
            >>> client = Client(
            ...     client_id="controller",
            ...     userdata={"device": "relay_board"}
            ... )
        ```
        """
    
    def username_pw_set(self, username: str, password: Optional[str] = None) -> None:
        """
        Set username and password for broker authentication.
        
        Configures authentication credentials for connecting to the MQTT broker.
        Must be called before connect() to take effect. Credentials are stored
        securely and sent during the CONNECT packet.
        
        :param username: Username for broker authentication
        :param password: Password for broker authentication (optional)
        
        Example
        -------
        ```python
            >>> client.username_pw_set("myuser", "mypassword")
            >>> client.connect("broker.example.com")
        ```
        """
    
    def tls_set(
        self,
        ca_certs: Optional[str] = None,
        certfile: Optional[str] = None,
        keyfile: Optional[str] = None,
        cert_reqs: Optional[int] = None,
        tls_version: Optional[int] = None,
        ciphers: Optional[str] = None
    ) -> None:
        """
        Configure TLS/SSL parameters for secure connections.
        
        Enables encrypted communication with the MQTT broker using TLS/SSL.
        Supports certificate-based authentication and custom cipher suites.
        Must be called before connect() to take effect.
        
        :param ca_certs: Path to CA certificate file for server verification
        :param certfile: Path to client certificate file (for mutual TLS)
        :param keyfile: Path to client private key file (for mutual TLS)
        :param cert_reqs: Certificate requirements (ssl.CERT_REQUIRED, etc.)
        :param tls_version: TLS protocol version (ssl.PROTOCOL_TLS, etc.)
        :param ciphers: Allowed cipher suites string
        
        Example
        -------
        ```python
            >>> # Basic TLS with server verification
            >>> client.tls_set(ca_certs="/flash/ca.crt")
            >>> 
            >>> # Mutual TLS authentication
            >>> client.tls_set(
            ...     ca_certs="/flash/ca.crt",
            ...     certfile="/flash/client.crt",
            ...     keyfile="/flash/client.key"
            ... )
        ```
        """
    
    def will_set(
        self,
        topic: str,
        payload: Union[str, bytes, None] = None,
        qos: int = 0,
        retain: bool = False,
        properties: Optional[Properties] = None
    ) -> None:
        """
        Set Last Will and Testament (LWT) message for unexpected disconnections.
        
        Configures a message that the broker will publish automatically if the
        client disconnects unexpectedly (e.g., network failure, power loss).
        Useful for notifying other clients about device status. Must be called
        before connect() to take effect.
        
        :param topic: Topic to publish LWT message to
        :param payload: LWT message payload (string or bytes)
        :param qos: Quality of Service level for LWT message (0, 1, or 2)
        :param retain: Retain flag for LWT message
        :param properties: MQTT 5.0 properties for LWT message
        
        Example
        -------
        ```python
            >>> # Simple offline status
            >>> client.will_set("devices/sensor001/status", "offline", qos=1, retain=True)
            >>> 
            >>> # LWT with MQTT 5.0 properties
            >>> props = Properties()
            >>> props.set("Content-Type", "application/json")
            >>> client.will_set(
            ...     "devices/sensor001/lwt",
            ...     '{"status":"disconnected","reason":"unexpected"}',
            ...     qos=1,
            ...     properties=props
            ... )
        ```
        """
    
    def will_clear(self) -> None:
        """
        Clear the previously configured Last Will and Testament message.
        
        Removes the LWT configuration. Must be called before connect() to take effect.
        
        Example
        -------
        ```python
            >>> client.will_clear()
        ```
        """
    
    def reconnect_delay_set(self, min_delay: int = 1, max_delay: int = 120) -> None:
        """
        Set reconnection delay parameters for automatic reconnection.
        
        Configures the minimum and maximum delays for exponential backoff
        reconnection attempts. The delay doubles with each failed attempt
        until reaching max_delay.
        
        :param min_delay: Minimum delay in seconds between reconnection attempts
        :param max_delay: Maximum delay in seconds between reconnection attempts
        
        Example
        -------
        ```python
            >>> # Start with 5s, max 60s
            >>> client.reconnect_delay_set(min_delay=5, max_delay=60)
        ```
        """
    
    def max_inflight_messages_set(self, inflight: int = 20) -> None:
        """
        Set maximum number of inflight messages for QoS 1 and 2.
        
        Limits the number of messages with QoS>0 that can be in the process
        of being transmitted simultaneously. Helps prevent memory exhaustion
        on resource-constrained devices.
        
        :param inflight: Maximum number of inflight messages (1-65535)
        
        Example
        -------
        ```python
            >>> client.max_inflight_messages_set(10)
        ```
        """
    
    def message_retry_set(self, retry: int = 5) -> None:
        """
        Set message retry interval in seconds for QoS 1 and 2.
        
        Configures how long to wait before retrying unacknowledged messages.
        Only applies to messages with QoS > 0.
        
        :param retry: Retry interval in seconds
        
        Example
        -------
        ```python
            >>> client.message_retry_set(10)
        ```
        """
    
    def user_data_set(self, userdata: Any) -> None:
        """
        Set or update user-defined data passed to callbacks.
        
        User data is passed as the second parameter to all callback functions,
        allowing you to access application-specific context within callbacks.
        
        :param userdata: Any user-defined data object
        
        Example
        -------
        ```python
            >>> client.user_data_set({"temperature_pin": 26, "led_pin": 25})
        ```
        """
    
    def connect(
        self,
        host: str,
        port: int = 1883,
        keepalive: int = 60,
        bind_address: str = ""
    ) -> int:
        """
        Connect to an MQTT broker and wait for connection to complete.
        
        Establishes a connection to the specified MQTT broker. This is a blocking
        call that waits for the connection to be established or fail. The
        on_connect callback will be called upon successful connection.
        
        :param host: Hostname or IP address of the MQTT broker
        :param port: Network port of the broker (1883 for TCP, 8883 for TLS)
        :param keepalive: Maximum period in seconds between communications with broker
        :param bind_address: Local network address to bind to (empty=any)
        
        :return: 0 on success, error code on failure
        
        :raises OSError: If connection fails (ETIMEDOUT, ECONNREFUSED, etc.)
        
        Example
        -------
        ```python
            >>> # Connect to public broker
            >>> rc = client.connect("test.mosquitto.org", 1883, 60)
            >>> if rc == 0:
            ...     print("Connected successfully")
            >>> 
            >>> # Connect to TLS broker
            >>> client.tls_set(ca_certs="/flash/ca.crt")
            >>> client.connect("mqtt.example.com", 8883)
        ```
        """
    
    def connect_async(
        self,
        host: str,
        port: int = 1883,
        keepalive: int = 60,
        bind_address: str = ""
    ) -> int:
        """
        Connect to an MQTT broker without waiting for completion.
        
        Initiates a connection to the MQTT broker but returns immediately
        without waiting for the connection to complete. You must call loop()
        or loop_forever() to complete the connection. The on_connect callback
        will be called when connection succeeds.
        
        :param host: Hostname or IP address of the MQTT broker
        :param port: Network port of the broker (1883 for TCP, 8883 for TLS)
        :param keepalive: Maximum period in seconds between communications with broker
        :param bind_address: Local network address to bind to (empty=any)
        
        :return: 0 on success, error code on failure
        
        Example
        -------
        ```python
            >>> client.connect_async("mqtt.example.com", 1883)
            >>> client.loop_forever()  # Connection completes here
        ```
        """
    
    def reconnect(self) -> int:
        """
        Reconnect to the broker using previously saved connection parameters.
        
        Attempts to re-establish a connection using the same parameters from
        the previous connect() or connect_async() call. Useful for handling
        connection failures or implementing custom reconnection logic.
        
        :return: 0 on success, error code on failure
        
        Example
        -------
        ```python
            >>> if not client.is_connected():
            ...     rc = client.reconnect()
            ...     if rc != 0:
            ...         print("Reconnection failed")
        ```
        """
    
    def disconnect(
        self,
        reasoncode: Optional[int] = None,
        properties: Optional[Properties] = None
    ) -> int:
        """
        Disconnect from the MQTT broker gracefully.
        
        Sends a DISCONNECT packet to the broker and closes the connection.
        The broker will NOT publish the LWT message for graceful disconnects.
        The on_disconnect callback will be called after disconnection completes.
        
        :param reasoncode: MQTT 5.0 reason code for disconnection (optional)
        :param properties: MQTT 5.0 properties for DISCONNECT packet (optional)
        
        :return: 0 on success, error code on failure
        
        Example
        -------
        ```python
            >>> client.disconnect()
            >>> print("Disconnected from broker")
        ```
        """
    
    def publish(
        self,
        topic: str,
        payload: Union[str, bytes, None] = None,
        qos: int = 0,
        retain: bool = False,
        properties: Optional[Properties] = None
    ) -> MQTTMessageInfo:
        """
        Publish a message to the broker on the specified topic.
        
        Sends a message to the MQTT broker for distribution to subscribers.
        The behavior depends on the QoS level:
        - QoS 0: Fire-and-forget, returns immediately
        - QoS 1: Waits for PUBACK acknowledgment
        - QoS 2: Waits for PUBREC/PUBREL/PUBCOMP 4-way handshake
        
        Returns a MQTTMessageInfo object for tracking message delivery status.
        The on_publish callback is called when the message is acknowledged.
        
        :param topic: Topic to publish message to (must not contain wildcards)
        :param payload: Message payload (string, bytes, or None for empty)
        :param qos: Quality of Service level (0, 1, or 2)
        :param retain: If True, broker retains message for future subscribers
        :param properties: MQTT 5.0 properties for PUBLISH packet (optional)
        
        :return: MQTTMessageInfo object for tracking delivery
        
        :raises ValueError: If topic is invalid or contains wildcards
        
        Example
        -------
        ```python
            >>> # Simple publish (QoS 0)
            >>> client.publish("sensors/temperature", "23.5")
            >>> 
            >>> # Publish with QoS 1 and retain
            >>> info = client.publish("status/online", "true", qos=1, retain=True)
            >>> info.wait_for_publish()  # Block until acknowledged
            >>> 
            >>> # Publish with MQTT 5.0 properties
            >>> props = Properties()
            >>> props.set("Content-Type", "application/json")
            >>> props.set("Message-Expiry-Interval", 3600)
            >>> client.publish(
            ...     "data/sensor",
            ...     '{"temp":23.5,"hum":65}',
            ...     qos=1,
            ...     properties=props
            ... )
        ```
        """
    
    def subscribe(
        self,
        topic: Union[str, Tuple[str, int], List[Tuple[str, int]]],
        qos: int = 0,
        options: Optional[Any] = None,
        properties: Optional[Properties] = None
    ) -> Tuple[int, int]:
        """
        Subscribe to one or more topics on the broker.
        
        Requests the broker to send messages matching the specified topic(s)
        to this client. Supports wildcard subscriptions using + (single level)
        and # (multi-level). The on_subscribe callback is called when the
        subscription is acknowledged. Received messages trigger on_message callback.
        
        :param topic: Single topic string, (topic, qos) tuple, or list of tuples
        :param qos: Default QoS level if topic is a string (0, 1, or 2)
        :param options: Subscription options (MQTT 5.0)
        :param properties: MQTT 5.0 properties for SUBSCRIBE packet
        
        :return: Tuple of (result_code, message_id)
        
        Example
        -------
        ```python
            >>> # Single topic subscription
            >>> client.subscribe("sensors/temperature", qos=1)
            >>> 
            >>> # Multiple topics with different QoS
            >>> client.subscribe([
            ...     ("sensors/temperature", 1),
            ...     ("sensors/humidity", 1),
            ...     ("alerts/#", 2)
            ... ])
            >>> 
            >>> # Wildcard subscriptions
            >>> client.subscribe("sensors/+/data", qos=1)  # Single level
            >>> client.subscribe("devices/#", qos=0)        # Multi-level
        ```
        """
    
    def unsubscribe(
        self,
        topic: Union[str, List[str]],
        properties: Optional[Properties] = None
    ) -> Tuple[int, int]:
        """
        Unsubscribe from one or more topics on the broker.
        
        Requests the broker to stop sending messages for the specified topic(s).
        The on_unsubscribe callback is called when the unsubscription is acknowledged.
        
        :param topic: Single topic string or list of topic strings
        :param properties: MQTT 5.0 properties for UNSUBSCRIBE packet
        
        :return: Tuple of (result_code, message_id)
        
        Example
        -------
        ```python
            >>> # Unsubscribe from single topic
            >>> client.unsubscribe("sensors/temperature")
            >>> 
            >>> # Unsubscribe from multiple topics
            >>> client.unsubscribe([
            ...     "sensors/temperature",
            ...     "sensors/humidity"
            ... ])
        ```
        """
    
    def loop(self, timeout: float = 1.0, max_packets: int = 1) -> int:
        """
        Process network traffic and dispatch callbacks for a single iteration.
        
        Handles incoming/outgoing messages, processes acknowledgments, and
        maintains the connection. Must be called regularly to keep the connection
        alive and handle messages. Use this in your main application loop when
        you need to do other processing between MQTT operations.
        
        :param timeout: Maximum time in seconds to block waiting for network traffic
        :param max_packets: Maximum number of packets to process in this call
        
        :return: 0 on success, error code on failure
        
        Example
        -------
        ```python
            >>> import time
            >>> client.connect("mqtt.example.com")
            >>> client.subscribe("sensors/#")
            >>> 
            >>> while True:
            ...     client.loop(timeout=1.0)
            ...     # Do other application work here
            ...     read_sensors()
            ...     time.sleep(0.1)
        ```
        """
    
    def loop_forever(
        self,
        timeout: float = 1.0,
        max_packets: int = 1,
        retry_first_connection: bool = False
    ) -> int:
        """
        Run the network loop indefinitely, blocking until disconnect.
        
        Continuously calls loop() in an infinite loop until disconnect() is called
        or an error occurs. Handles automatic reconnection if configured. Use this
        when MQTT is the primary function of your application.
        
        :param timeout: Maximum time in seconds to block per loop iteration
        :param max_packets: Maximum number of packets to process per iteration
        :param retry_first_connection: Keep retrying if initial connection fails
        
        :return: 0 on normal exit, error code on failure
        
        Example
        -------
        ```python
            >>> def on_message(client, userdata, msg):
            ...     print(f"{msg.topic}: {msg.payload}")
            >>> 
            >>> client.on_message = on_message
            >>> client.connect("mqtt.example.com")
            >>> client.subscribe("alerts/#")
            >>> client.loop_forever()  # Blocks until disconnect
        ```
        """
    
    def loop_start(self) -> None:
        """
        Start a background thread to automatically call loop().
        
        Note: Threading is not supported in MicroPython. This method
        is provided for API compatibility but will raise NotImplementedError.
        Use loop() or loop_forever() instead.
        
        :raises NotImplementedError: Always (threading not supported)
        """
    
    def loop_stop(self, force: bool = False) -> None:
        """
        Stop the background thread started by loop_start().
        
        Note: Threading is not supported in MicroPython. This method
        is provided for API compatibility but will raise NotImplementedError.
        
        :param force: Force stop even if thread is busy
        
        :raises NotImplementedError: Always (threading not supported)
        """
    
    def message_callback_add(self, sub: str, callback: Callable[[Client, Any, MQTTMessage], None]) -> None:
        """
        Register a topic-specific callback for received messages.
        
        Adds a callback function that will be called only for messages matching
        the specified topic pattern. Supports wildcard patterns. If a message
        matches multiple callbacks, all matching callbacks are called. If no
        topic-specific callback matches, the global on_message callback is used.
        
        :param sub: Topic pattern (supports + and # wildcards)
        :param callback: Function to call for matching messages
        
        Callback signature: callback(client, userdata, message)
        
        Example
        -------
        ```python
            >>> def handle_temperature(client, userdata, msg):
            ...     temp = float(msg.payload)
            ...     print(f"Temperature: {temp}°C")
            >>> 
            >>> def handle_alerts(client, userdata, msg):
            ...     print(f"ALERT: {msg.payload}")
            >>> 
            >>> client.message_callback_add("sensors/temperature", handle_temperature)
            >>> client.message_callback_add("alerts/#", handle_alerts)
        ```
        """
    
    def message_callback_remove(self, sub: str) -> None:
        """
        Remove a previously registered topic-specific callback.
        
        Removes the callback for the specified topic pattern. Messages matching
        this pattern will fall back to the global on_message callback.
        
        :param sub: Topic pattern to remove callback for
        
        Example
        -------
        ```python
            >>> client.message_callback_remove("sensors/temperature")
        ```
        """
    
    def is_connected(self) -> bool:
        """
        Check if the client is currently connected to the broker.
        
        Returns the current connection status based on internal state tracking.
        Use this to verify connectivity before performing operations that require
        an active connection.
        
        :return: True if connected, False otherwise
        
        Example
        -------
        ```python
            >>> if client.is_connected():
            ...     client.publish("status", "online")
            ... else:
            ...     print("Not connected, attempting reconnect...")
            ...     client.reconnect()
        ```
        """
