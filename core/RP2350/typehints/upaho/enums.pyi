"""
Module: 'upaho.enums' on micropython-v1.25.0-rp2-RPI_PICO2_W

MQTT Protocol Enumerations and Constants
"""
# MCU: {'build': '', 'ver': '1.25.0', 'version': '1.25.0', 'port': 'rp2', 'board': 'RPI_PICO2_W', 'mpy': 'v6.3', 'family': 'micropython', 'cpu': 'RP2350', 'arch': 'armv7emsp'}
# Stubber: v1.24.0

from __future__ import annotations
from typing import Optional

class MQTTProtocolVersion:
    """
    MQTT protocol version constants.
    
    Supported versions:
        - MQTTv31: MQTT 3.1 (legacy)
        - MQTTv311: MQTT 3.1.1 (widely supported)
        - MQTTv5: MQTT 5.0 (latest with enhanced features)
    
    Example
    -------
    ```python
        >>> # Use MQTT 5.0
        >>> client = Client(protocol=MQTTProtocolVersion.MQTTv5)
        >>> 
        >>> # Fallback to MQTT 3.1.1 for compatibility
        >>> legacy_client = Client(protocol=MQTTProtocolVersion.MQTTv311)
    ```
    """
    MQTTv31: int
    MQTTv311: int
    MQTTv5: int

class PacketType:
    """
    MQTT packet type identifiers.
    
    All MQTT packet types defined in the protocol specification.
    These are used internally for packet encoding/decoding.
    
    Control Packets:
        - CONNECT: Client connection request
        - CONNACK: Connection acknowledgment
        - DISCONNECT: Graceful disconnection
        - AUTH: Authentication exchange (MQTT 5.0)
        - PINGREQ: Keepalive ping request
        - PINGRESP: Keepalive ping response
    
    Publish/Subscribe:
        - PUBLISH: Publish message
        - PUBACK: QoS 1 publish acknowledgment
        - PUBREC: QoS 2 publish received
        - PUBREL: QoS 2 publish release
        - PUBCOMP: QoS 2 publish complete
        - SUBSCRIBE: Subscribe to topics
        - SUBACK: Subscribe acknowledgment
        - UNSUBSCRIBE: Unsubscribe from topics
        - UNSUBACK: Unsubscribe acknowledgment
    """
    RESERVED_0: int
    CONNECT: int
    CONNACK: int
    PUBLISH: int
    PUBACK: int
    PUBREC: int
    PUBREL: int
    PUBCOMP: int
    SUBSCRIBE: int
    SUBACK: int
    UNSUBSCRIBE: int
    UNSUBACK: int
    PINGREQ: int
    PINGRESP: int
    DISCONNECT: int
    AUTH: int

class ReasonCode:
    """
    MQTT 5.0 reason codes for operation results.
    
    Reason codes provide detailed information about the result of MQTT
    operations. They appear in CONNACK, PUBACK, SUBACK, DISCONNECT,
    and other acknowledgment packets.
    
    Success Codes:
        - SUCCESS (0): Operation completed successfully
        - NORMAL_DISCONNECTION (0): Clean disconnect
        - GRANTED_QOS_0 (0): Subscription granted with QoS 0
        - GRANTED_QOS_1 (1): Subscription granted with QoS 1
        - GRANTED_QOS_2 (2): Subscription granted with QoS 2
    
    Client-Side Errors (0x80-0x9F):
        - UNSPECIFIED_ERROR: Generic error
        - MALFORMED_PACKET: Packet format invalid
        - PROTOCOL_ERROR: Protocol violation
        - IMPLEMENTATION_SPECIFIC_ERROR: Implementation limit exceeded
        - UNSUPPORTED_PROTOCOL_VERSION: Protocol version not supported
        - CLIENT_IDENTIFIER_NOT_VALID: Invalid client ID
        - BAD_USER_NAME_OR_PASSWORD: Authentication failed
        - NOT_AUTHORIZED: Not authorized for operation
        - TOPIC_FILTER_INVALID: Subscription topic invalid
        - TOPIC_NAME_INVALID: Publish topic invalid
        - PACKET_IDENTIFIER_IN_USE: Duplicate message ID
        - PACKET_TOO_LARGE: Message exceeds maximum size
        - QUOTA_EXCEEDED: Client quota limit exceeded
        - PAYLOAD_FORMAT_INVALID: Payload format doesn't match indicator
        - RETAIN_NOT_SUPPORTED: Retain not supported
        - QOS_NOT_SUPPORTED: Requested QoS not supported
        - WILDCARD_SUBSCRIPTIONS_NOT_SUPPORTED: Wildcards not allowed
        - SUBSCRIPTION_IDENTIFIERS_NOT_SUPPORTED: Feature not available
    
    Server-Side Errors (0xA0-0xBF):
        - SERVER_UNAVAILABLE: Server temporarily unavailable
        - SERVER_BUSY: Server overloaded
        - BANNED: Client banned from server
        - SERVER_SHUTTING_DOWN: Server is shutting down
        - BAD_AUTHENTICATION_METHOD: Authentication method not supported
        - KEEP_ALIVE_TIMEOUT: Client keepalive timeout
        - SESSION_TAKEN_OVER: Another client with same ID connected
        - USE_ANOTHER_SERVER: Client should use different server
        - SERVER_MOVED: Server permanently moved
        - CONNECTION_RATE_EXCEEDED: Too many connections
        - MAXIMUM_CONNECT_TIME: Connection time limit exceeded
    
    Usage:
        Reason codes are automatically handled by the client and passed
        to callbacks. Check the code in on_connect, on_disconnect, etc.
    
    Example
    -------
    ```python
        >>> def on_connect(client, userdata, flags, rc, properties):
        ...     if rc == ReasonCode.SUCCESS:
        ...         print("Connected successfully")
        ...         client.subscribe("sensors/#")
        ...     elif rc == ReasonCode.BAD_USER_NAME_OR_PASSWORD:
        ...         print("Authentication failed")
        ...     elif rc == ReasonCode.NOT_AUTHORIZED:
        ...         print("Not authorized")
        ...     else:
        ...         print(f"Connection failed: {reason_code_to_string(rc)}")
    ```
    """
    SUCCESS: int
    NORMAL_DISCONNECTION: int
    GRANTED_QOS_0: int
    GRANTED_QOS_1: int
    GRANTED_QOS_2: int
    DISCONNECT_WITH_WILL_MESSAGE: int
    NO_MATCHING_SUBSCRIBERS: int
    NO_SUBSCRIPTION_EXISTED: int
    CONTINUE_AUTHENTICATION: int
    RE_AUTHENTICATE: int
    UNSPECIFIED_ERROR: int
    MALFORMED_PACKET: int
    PROTOCOL_ERROR: int
    IMPLEMENTATION_SPECIFIC_ERROR: int
    UNSUPPORTED_PROTOCOL_VERSION: int
    CLIENT_IDENTIFIER_NOT_VALID: int
    BAD_USER_NAME_OR_PASSWORD: int
    NOT_AUTHORIZED: int
    SERVER_UNAVAILABLE: int
    SERVER_BUSY: int
    BANNED: int
    SERVER_SHUTTING_DOWN: int
    BAD_AUTHENTICATION_METHOD: int
    KEEP_ALIVE_TIMEOUT: int
    SESSION_TAKEN_OVER: int
    TOPIC_FILTER_INVALID: int
    TOPIC_NAME_INVALID: int
    PACKET_IDENTIFIER_IN_USE: int
    PACKET_IDENTIFIER_NOT_FOUND: int
    RECEIVE_MAXIMUM_EXCEEDED: int
    TOPIC_ALIAS_INVALID: int
    PACKET_TOO_LARGE: int
    MESSAGE_RATE_TOO_HIGH: int
    QUOTA_EXCEEDED: int
    ADMINISTRATIVE_ACTION: int
    PAYLOAD_FORMAT_INVALID: int
    RETAIN_NOT_SUPPORTED: int
    QOS_NOT_SUPPORTED: int
    USE_ANOTHER_SERVER: int
    SERVER_MOVED: int
    SHARED_SUBSCRIPTIONS_NOT_SUPPORTED: int
    CONNECTION_RATE_EXCEEDED: int
    MAXIMUM_CONNECT_TIME: int
    SUBSCRIPTION_IDENTIFIERS_NOT_SUPPORTED: int
    WILDCARD_SUBSCRIPTIONS_NOT_SUPPORTED: int

class QoS:
    """
    Quality of Service levels for message delivery.
    
    MQTT defines three QoS levels that determine message delivery guarantees:
    
    QoS 0 (AT_MOST_ONCE):
        - Fire-and-forget delivery
        - No acknowledgment from broker
        - Fastest but may lose messages
        - Best for: High-frequency sensor data where occasional loss is acceptable
    
    QoS 1 (AT_LEAST_ONCE):
        - Guaranteed delivery with acknowledgment (PUBACK)
        - Message may be delivered multiple times
        - Balance of reliability and performance
        - Best for: Important data where duplicates can be handled
    
    QoS 2 (EXACTLY_ONCE):
        - Guaranteed exactly-once delivery
        - 4-way handshake: PUBREC → PUBREL → PUBCOMP
        - Highest reliability but slowest
        - Best for: Critical data where duplicates are unacceptable (billing, commands)
    
    Performance Characteristics:
        - QoS 0: 581 msg/s, no overhead
        - QoS 1: 68.7 msg/s, 1 ACK per message
        - QoS 2: Slower, 3 ACKs per message (4-way handshake)
    
    Example
    -------
    ```python
        >>> # High-frequency sensor data (losses acceptable)
        >>> client.publish("sensors/temp", str(temp), qos=QoS.AT_MOST_ONCE)
        >>> 
        >>> # Important status updates (ensure delivery)
        >>> client.publish("status/online", "true", qos=QoS.AT_LEAST_ONCE, retain=True)
        >>> 
        >>> # Critical commands (exactly-once delivery)
        >>> client.publish("commands/unlock", "door_1", qos=QoS.EXACTLY_ONCE)
        >>> 
        >>> # Subscribe with QoS 1 for reliable data
        >>> client.subscribe("alerts/#", qos=QoS.AT_LEAST_ONCE)
    ```
    """
    AT_MOST_ONCE: int
    AT_LEAST_ONCE: int
    EXACTLY_ONCE: int

class PropertyType:
    """
    MQTT 5.0 property type identifiers.
    
    Property types define the metadata that can be attached to MQTT packets.
    Each property has a specific data type and usage context.
    
    Message Properties:
        - PAYLOAD_FORMAT_INDICATOR: 0=bytes, 1=UTF-8 text
        - CONTENT_TYPE: MIME type of payload
        - MESSAGE_EXPIRY_INTERVAL: Seconds until message expires
        - CORRELATION_DATA: Request-response correlation
        - RESPONSE_TOPIC: Topic for response messages
    
    Connection Properties:
        - SESSION_EXPIRY_INTERVAL: Session persistence time
        - SERVER_KEEP_ALIVE: Server-assigned keepalive
        - RECEIVE_MAXIMUM: Max inflight QoS 1/2 messages
        - MAXIMUM_PACKET_SIZE: Max packet size in bytes
        - ASSIGNED_CLIENT_IDENTIFIER: Server-assigned client ID
    
    Authentication:
        - AUTHENTICATION_METHOD: Authentication mechanism name
        - AUTHENTICATION_DATA: Authentication data bytes
    
    Topic Management:
        - TOPIC_ALIAS: Integer alias for topic (bandwidth optimization)
        - TOPIC_ALIAS_MAXIMUM: Max topic aliases supported
    
    User-Defined:
        - USER_PROPERTY: Custom key-value pairs (can be multiple)
    
    Server Information:
        - REASON_STRING: Human-readable reason for response
        - SERVER_REFERENCE: Alternative server hostname
        - RESPONSE_INFORMATION: Response topic pattern
    
    Feature Flags:
        - REQUEST_PROBLEM_INFORMATION: Request reason strings
        - REQUEST_RESPONSE_INFORMATION: Request response info
        - WILDCARD_SUBSCRIPTION_AVAILABLE: Server supports wildcards
        - SUBSCRIPTION_IDENTIFIER_AVAILABLE: Server supports sub IDs
        - SHARED_SUBSCRIPTION_AVAILABLE: Server supports shared subs
        - RETAIN_AVAILABLE: Server supports retained messages
        - MAXIMUM_QOS: Maximum QoS level supported
    """
    PAYLOAD_FORMAT_INDICATOR: int
    MESSAGE_EXPIRY_INTERVAL: int
    CONTENT_TYPE: int
    RESPONSE_TOPIC: int
    CORRELATION_DATA: int
    SUBSCRIPTION_IDENTIFIER: int
    SESSION_EXPIRY_INTERVAL: int
    ASSIGNED_CLIENT_IDENTIFIER: int
    SERVER_KEEP_ALIVE: int
    AUTHENTICATION_METHOD: int
    AUTHENTICATION_DATA: int
    REQUEST_PROBLEM_INFORMATION: int
    WILL_DELAY_INTERVAL: int
    REQUEST_RESPONSE_INFORMATION: int
    RESPONSE_INFORMATION: int
    SERVER_REFERENCE: int
    REASON_STRING: int
    RECEIVE_MAXIMUM: int
    TOPIC_ALIAS_MAXIMUM: int
    TOPIC_ALIAS: int
    MAXIMUM_QOS: int
    RETAIN_AVAILABLE: int
    USER_PROPERTY: int
    MAXIMUM_PACKET_SIZE: int
    WILDCARD_SUBSCRIPTION_AVAILABLE: int
    SUBSCRIPTION_IDENTIFIER_AVAILABLE: int
    SHARED_SUBSCRIPTION_AVAILABLE: int

class ConnectFlag:
    """
    CONNECT packet flag bits.
    
    These flags are used internally in the CONNECT packet to specify
    connection options and capabilities.
    
    Flags:
        - USERNAME: Username present in payload
        - PASSWORD: Password present in payload
        - WILL_RETAIN: Last Will message should be retained
        - WILL_QOS_1: Will QoS bit 1
        - WILL_QOS_2: Will QoS bit 2
        - WILL_FLAG: Last Will message present
        - CLEAN_START: Start with clean session (MQTT 5.0)
    
    Example
    -------
    ```python
        >>> # Typically used internally by client
        >>> # When username/password are set:
        >>> client.username_pw_set("user", "pass")
        >>> # USERNAME and PASSWORD flags are set automatically
    ```
    """
    USERNAME: int
    PASSWORD: int
    WILL_RETAIN: int
    WILL_QOS_1: int
    WILL_QOS_2: int
    WILL_FLAG: int
    CLEAN_START: int

def reason_code_to_string(code: int) -> Optional[str]:
    """
    Convert a reason code integer to its human-readable name.
    
    Provides a convenient way to get descriptive names for MQTT 5.0
    reason codes, useful for logging and debugging.
    
    :param code: Reason code integer
    
    :return: String name of the reason code, or None if unknown
    
    Example
    -------
    ```python
        >>> def on_connect(client, userdata, flags, rc, properties):
        ...     if rc != 0:
        ...         print(f"Connection failed: {reason_code_to_string(rc)}")
        ...         # Output: "Connection failed: Bad User Name or Password"
        >>> 
        >>> # Logging disconnect reasons
        >>> def on_disconnect(client, userdata, rc, properties):
        ...     reason = reason_code_to_string(rc) or f"Unknown ({rc})"
        ...     print(f"Disconnected: {reason}")
    ```
    """
