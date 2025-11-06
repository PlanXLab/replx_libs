from __future__ import annotations
from typing import Optional, Callable, Any, Dict, Tuple, List, Union
from .enums import MQTTProtocolVersion, ReasonCode
from .properties import Properties
from .message import MQTTMessage, MQTTMessageInfo

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"

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
    
    Callback Attributes
    -------------------
    
    These callbacks can be set to handle MQTT events. All callbacks receive
    the client instance and userdata as first parameters.
    """
    
    on_connect: Optional[Callable[[Client, Any, Dict, int, Optional[Properties]], None]]
    """
    Callback when connection is established or connection attempt fails.
    
    Called when the broker responds to our connection request. Use this to
    subscribe to topics or perform any initialization that requires an
    active connection.
    
    Parameters
    ----------
    client : Client
        The client instance for this callback
    userdata : Any
        User-defined data passed during client initialization
    flags : Dict
        Response flags from broker, contains:
        - 'session_present': bool - True if broker has previous session state
    rc : int
        Connection result code (ReasonCode.SUCCESS = 0 for success)
    properties : Optional[Properties]
        MQTT 5.0 properties from CONNACK (None for MQTT 3.1.1)
    
    Returns
    -------
    None
    
    Example
    -------
    ```python
        >>> def on_connect(client, userdata, flags, rc, properties):
        ...     if rc == 0:
        ...         print("Connected successfully!")
        ...         if flags.get('session_present'):
        ...             print("Resuming previous session")
        ...         # Subscribe to topics
        ...         client.subscribe("sensors/#", qos=1)
        ...     else:
        ...         print(f"Connection failed with code {rc}")
        >>> 
        >>> client = Client()
        >>> client.on_connect = on_connect
        >>> client.connect("broker.example.com")
    ```
    """
    
    on_disconnect: Optional[Callable[[Client, Any, int, Optional[Properties]], None]]
    """
    Callback when client disconnects from broker.
    
    Called when the client disconnects from the broker, either due to calling
    disconnect() or due to an unexpected network issue. Use this to implement
    reconnection logic or cleanup.
    
    Parameters
    ----------
    client : Client
        The client instance for this callback
    userdata : Any
        User-defined data passed during client initialization
    rc : int
        Disconnection reason code:
        - ReasonCode.SUCCESS (0): Normal disconnection
        - ReasonCode.KEEPALIVE_TIMEOUT: Keepalive timeout
        - ReasonCode.NETWORK_ERROR: Network issue
        - ReasonCode.PROTOCOL_ERROR: Protocol error
    properties : Optional[Properties]
        MQTT 5.0 properties from DISCONNECT (None for MQTT 3.1.1)
    
    Returns
    -------
    None
    
    Example
    -------
    ```python
        >>> def on_disconnect(client, userdata, rc, properties):
        ...     if rc != 0:
        ...         print(f"Unexpected disconnect: {rc}")
        ...         # Implement reconnection logic
        ...         time.sleep(5)
        ...         client.reconnect()
        ...     else:
        ...         print("Disconnected normally")
        >>> 
        >>> client.on_disconnect = on_disconnect
    ```
    """
    
    on_message: Optional[Callable[[Client, Any, MQTTMessage], None]]
    """
    Callback when a message is received from broker.
    
    Called when a PUBLISH message is received for a subscribed topic that
    doesn't have a topic-specific callback. This is the default message handler.
    
    Parameters
    ----------
    client : Client
        The client instance for this callback
    userdata : Any
        User-defined data passed during client initialization
    message : MQTTMessage
        The received message containing:
        - topic: str - Message topic
        - payload: bytes - Message payload
        - qos: int - Quality of Service level (0, 1, or 2)
        - retain: bool - Whether message was retained
        - mid: int - Message identifier (for QoS > 0)
        - properties: Properties - MQTT 5.0 properties
    
    Returns
    -------
    None
    
    Example
    -------
    ```python
        >>> def on_message(client, userdata, msg):
        ...     print(f"Received on {msg.topic}")
        ...     print(f"Payload: {msg.payload.decode()}")
        ...     print(f"QoS: {msg.qos}")
        ...     
        ...     # Handle different topics
        ...     if msg.topic.startswith("sensors/"):
        ...         sensor_data = json.loads(msg.payload)
        ...         process_sensor(sensor_data)
        >>> 
        >>> client.on_message = on_message
    ```
    
    See Also
    --------
    message_callback_add : Add topic-specific message callbacks
    """
    
    on_publish: Optional[Callable[[Client, Any, int], None]]
    """
    Callback when a message has been successfully sent to broker.
    
    Called when a message with QoS 1 or QoS 2 has been successfully delivered
    and acknowledged. For QoS 0, this is called immediately after sending.
    For QoS 1, called after PUBACK. For QoS 2, called after PUBCOMP.
    
    Parameters
    ----------
    client : Client
        The client instance for this callback
    userdata : Any
        User-defined data passed during client initialization
    mid : int
        Message identifier of the published message
    
    Returns
    -------
    None
    
    Example
    -------
    ```python
        >>> published_messages = {}
        >>> 
        >>> def on_publish(client, userdata, mid):
        ...     print(f"Message {mid} delivered successfully")
        ...     if mid in published_messages:
        ...         msg_info = published_messages.pop(mid)
        ...         print(f"Confirmed: {msg_info}")
        >>> 
        >>> client.on_publish = on_publish
        >>> 
        >>> # Publish and track
        >>> info = client.publish("test/topic", "data", qos=1)
        >>> published_messages[info.mid] = "Temperature reading"
    ```
    
    See Also
    --------
    publish : Publish a message to the broker
    MQTTMessageInfo : Return value from publish() with status tracking
    """
    
    on_subscribe: Optional[Callable[[Client, Any, int, List[int], Optional[Properties]], None]]
    """
    Callback when subscription is acknowledged by broker.
    
    Called when the broker responds to a SUBSCRIBE request with SUBACK,
    indicating which subscriptions were granted and at what QoS levels.
    
    Parameters
    ----------
    client : Client
        The client instance for this callback
    userdata : Any
        User-defined data passed during client initialization
    mid : int
        Message identifier of the subscribe request
    granted_qos : List[int]
        List of granted QoS levels for each subscription:
        - 0: QoS 0 granted
        - 1: QoS 1 granted
        - 2: QoS 2 granted
        - 0x80 (128): Subscription failure
    properties : Optional[Properties]
        MQTT 5.0 properties from SUBACK (None for MQTT 3.1.1)
    
    Returns
    -------
    None
    
    Example
    -------
    ```python
        >>> def on_subscribe(client, userdata, mid, granted_qos, properties):
        ...     print(f"Subscription {mid} acknowledged")
        ...     for i, qos in enumerate(granted_qos):
        ...         if qos == 0x80:
        ...             print(f"  Topic {i}: Subscription FAILED")
        ...         else:
        ...             print(f"  Topic {i}: Granted QoS {qos}")
        >>> 
        >>> client.on_subscribe = on_subscribe
        >>> 
        >>> # Subscribe to multiple topics
        >>> client.subscribe([
        ...     ("sensors/temp", 0),
        ...     ("sensors/humidity", 1),
        ...     ("alerts/#", 2)
        ... ])
    ```
    """
    
    on_unsubscribe: Optional[Callable[[Client, Any, int, Optional[Properties]], None]]
    """
    Callback when unsubscription is acknowledged by broker.
    
    Called when the broker responds to an UNSUBSCRIBE request with UNSUBACK,
    confirming that the subscriptions have been removed.
    
    Parameters
    ----------
    client : Client
        The client instance for this callback
    userdata : Any
        User-defined data passed during client initialization
    mid : int
        Message identifier of the unsubscribe request
    properties : Optional[Properties]
        MQTT 5.0 properties from UNSUBACK (None for MQTT 3.1.1)
    
    Returns
    -------
    None
    
    Example
    -------
    ```python
        >>> def on_unsubscribe(client, userdata, mid, properties):
        ...     print(f"Unsubscription {mid} confirmed")
        ...     print("Successfully unsubscribed from topics")
        >>> 
        >>> client.on_unsubscribe = on_unsubscribe
        >>> client.unsubscribe(["sensors/temp", "sensors/humidity"])
    ```
    """
    
    on_log: Optional[Callable[[Client, Any, int, str], None]]
    """
    Callback for logging and debugging.
    
    Called when the client has log information. Use this for debugging,
    monitoring, or custom logging implementations. Can be verbose.
    
    Parameters
    ----------
    client : Client
        The client instance for this callback
    userdata : Any
        User-defined data passed during client initialization
    level : int
        Log level:
        - 0: ERROR - Critical errors
        - 1: INFO - Informational messages
        - 2: DEBUG - Detailed debug information
    buf : str
        Log message text
    
    Returns
    -------
    None
    
    Example
    -------
    ```python
        >>> def on_log(client, userdata, level, buf):
        ...     level_names = ["ERROR", "INFO", "DEBUG"]
        ...     level_str = level_names[min(level, 2)]
        ...     print(f"[{level_str}] {buf}")
        >>> 
        >>> client.on_log = on_log
        >>> 
        >>> # Or use for file logging
        >>> import logging
        >>> logger = logging.getLogger("mqtt")
        >>> 
        >>> def on_log_to_file(client, userdata, level, buf):
        ...     if level == 0:
        ...         logger.error(buf)
        ...     elif level == 1:
        ...         logger.info(buf)
        ...     else:
        ...         logger.debug(buf)
        >>> 
        >>> client.on_log = on_log_to_file
    ```
    """
    
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
        keepalive: int = 60
    ) -> int:
        """
        Connect to an MQTT broker and wait for connection to complete.
        
        Establishes a connection to the specified MQTT broker. This is a blocking
        call that waits for the connection to be established or fail. The
        on_connect callback will be called upon successful connection.
        
        :param host: Hostname or IP address of the MQTT broker
        :param port: Network port of the broker (1883 for TCP, 8883 for TLS)
        :param keepalive: Maximum period in seconds between communications with broker
        
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
