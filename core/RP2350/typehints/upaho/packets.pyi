from __future__ import annotations
from typing import Optional, List, Tuple, Union
from .enums import PacketType, MQTTProtocolVersion, ReasonCode
from .properties import Properties

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class MQTTPacket:
    """
    Base class for all MQTT packet types.
    
    This abstract class defines the common interface for MQTT protocol packets,
    providing the foundation for encoding and decoding MQTT messages. Each
    packet type (CONNECT, PUBLISH, SUBSCRIBE, etc.) extends this class with
    specific implementation details.
    
    The class handles the fixed header construction that is common to all
    MQTT packets, including packet type identification and remaining length
    calculation using MQTT's variable-length encoding scheme.
    
    Attributes:
        packet_type: MQTT packet type identifier (from PacketType enum)
        flags: 4-bit flags in the fixed header (usage varies by packet type)
    """
    
    packet_type: int
    flags: int
    
    def __init__(self, packet_type: int, flags: int = 0) -> None:
        """
        Initialize MQTT packet with type and flags.
        
        :param packet_type: Packet type identifier (use PacketType enum values)
        :param flags: Control flags for the fixed header (default: 0)
        
        Example
        -------
        ```python
            >>> from upaho.enums import PacketType
            >>> packet = MQTTPacket(PacketType.PUBLISH, flags=0x02)
        ```
        """
    
    def pack(self) -> bytes:
        """
        Serialize the packet into bytes for transmission.
        
        Encodes the complete MQTT packet including fixed header, variable
        header, and payload into a byte sequence ready for network transmission.
        Each packet type implements this method according to MQTT specification.
        
        :return: Complete packet as bytes
        :raises NotImplementedError: If called on base class
        
        Example
        -------
        ```python
            >>> packet = PingReqPacket()
            >>> data = packet.pack()
            >>> len(data)  # PINGREQ is 2 bytes
            2
        ```
        """
    
    def _pack_fixed_header(self, remaining_length: int) -> bytes:
        """
        Pack the MQTT fixed header with packet type and remaining length.
        
        Creates the fixed header consisting of:
        - Byte 1: Packet type (upper 4 bits) + flags (lower 4 bits)
        - Remaining bytes: Variable-length encoded remaining length
        
        :param remaining_length: Number of bytes following the fixed header
        :return: Encoded fixed header bytes
        
        Example
        -------
        ```python
            >>> # Internal use - constructs 2-byte header for PINGREQ
            >>> header = packet._pack_fixed_header(0)
            >>> header
            b'\\xc0\\x00'
        ```
        """


class ConnectPacket(MQTTPacket):
    """
    MQTT CONNECT packet for establishing broker connection.
    
    Initiates an MQTT session with a broker, carrying all necessary connection
    parameters including client identification, authentication credentials,
    session persistence settings, and optional Last Will Testament (LWT).
    
    This is always the first packet sent by a client. The broker responds
    with a CONNACK packet indicating success or failure.
    
    Attributes:
        client_id: Unique client identifier (empty for server-assigned ID)
        clean_start: Whether to start fresh session (True) or resume (False)
        keepalive: Maximum seconds between client communications
        username: Optional authentication username
        password: Optional authentication password
        will_topic: Optional LWT topic
        will_payload: Optional LWT message payload
        will_qos: LWT Quality of Service level (0, 1, or 2)
        will_retain: Whether broker should retain LWT message
        protocol_version: MQTT protocol version to use
        properties: MQTT 5.0 properties for connection metadata
        will_properties: MQTT 5.0 properties for LWT message
    """
    
    client_id: str
    clean_start: bool
    keepalive: int
    username: Optional[str]
    password: Optional[str]
    will_topic: Optional[str]
    will_payload: Optional[bytes]
    will_qos: int
    will_retain: bool
    protocol_version: int
    properties: Properties
    will_properties: Properties
    
    def __init__(
        self,
        client_id: str,
        clean_start: bool = True,
        keepalive: int = 60,
        username: Optional[str] = None,
        password: Optional[str] = None,
        will_topic: Optional[str] = None,
        will_payload: Optional[bytes] = None,
        will_qos: int = 0,
        will_retain: bool = False,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Optional[Properties] = None,
        will_properties: Optional[Properties] = None
    ) -> None:
        """
        Create CONNECT packet with connection parameters.
        
        :param client_id: Client identifier (empty string for auto-generated)
        :param clean_start: Start clean session if True
        :param keepalive: Keepalive interval in seconds
        :param username: Optional username for authentication
        :param password: Optional password for authentication
        :param will_topic: Last Will Testament topic
        :param will_payload: Last Will Testament message
        :param will_qos: LWT QoS level (0-2)
        :param will_retain: Retain LWT message on broker
        :param protocol_version: MQTT protocol version
        :param properties: Connection properties (MQTT 5.0)
        :param will_properties: LWT properties (MQTT 5.0)
        
        Example
        -------
        ```python
            >>> # Basic connection
            >>> packet = ConnectPacket(
            ...     client_id="sensor001",
            ...     keepalive=60
            ... )
            >>> 
            >>> # With authentication and LWT
            >>> packet = ConnectPacket(
            ...     client_id="sensor001",
            ...     username="user",
            ...     password="pass",
            ...     will_topic="devices/sensor001/status",
            ...     will_payload=b"offline",
            ...     will_qos=1,
            ...     will_retain=True
            ... )
        ```
        """
    
    def pack(self) -> bytes:
        """
        Serialize CONNECT packet for transmission.
        
        :return: Complete CONNECT packet as bytes
        
        Example
        -------
        ```python
            >>> packet = ConnectPacket("client123")
            >>> data = packet.pack()
            >>> data[0] >> 4  # Packet type = 1 (CONNECT)
            1
        ```
        """


class ConnackPacket(MQTTPacket):
    """
    MQTT CONNACK packet - broker's response to CONNECT.
    
    Sent by the broker in response to a CONNECT packet. Indicates whether
    the connection was accepted or rejected, and whether a previous session
    is being resumed. For MQTT 5.0, includes reason codes and properties
    with additional broker capabilities and settings.
    
    Attributes:
        session_present: True if broker has previous session state
        return_code: Connection result (MQTT 3.1.1)
        reason_code: Connection result code (MQTT 5.0)
        properties: Additional connection metadata (MQTT 5.0)
    """
    
    session_present: bool
    return_code: int
    reason_code: int
    properties: Properties
    
    def __init__(
        self,
        session_present: bool = False,
        return_code: int = 0,
        reason_code: int = ReasonCode.SUCCESS
    ) -> None:
        """
        Create CONNACK packet.
        
        :param session_present: Whether session state exists
        :param return_code: MQTT 3.1.1 connection return code
        :param reason_code: MQTT 5.0 reason code
        
        Example
        -------
        ```python
            >>> # Successful connection with new session
            >>> packet = ConnackPacket(
            ...     session_present=False,
            ...     reason_code=ReasonCode.SUCCESS
            ... )
        ```
        """
    
    def pack(self) -> bytes:
        """
        Serialize CONNACK packet.
        
        :return: Complete CONNACK packet as bytes
        """
    
    @staticmethod
    def unpack(data: bytes) -> ConnackPacket:
        """
        Deserialize CONNACK packet from received data.
        
        :param data: Raw packet data (without fixed header)
        :return: Parsed CONNACK packet
        
        Example
        -------
        ```python
            >>> data = b'\\x00\\x00'  # No session, success
            >>> packet = ConnackPacket.unpack(data)
            >>> packet.session_present
            False
            >>> packet.reason_code
            0
        ```
        """


class PublishPacket(MQTTPacket):
    """
    MQTT PUBLISH packet for message publication.
    
    Carries application messages from publisher to broker or broker to
    subscriber. Supports three Quality of Service levels controlling
    delivery guarantees. Can include retain flag for persistent messages
    and duplicate flag for QoS retransmissions.
    
    The most frequently used packet type in MQTT applications.
    
    Attributes:
        topic: Topic name to publish to
        payload: Message payload (bytes or string)
        qos: Quality of Service level (0, 1, or 2)
        retain: Whether broker should retain message
        dup: Duplicate flag (set on retransmissions)
        mid: Message identifier (required for QoS > 0)
        protocol_version: MQTT protocol version
        properties: Message metadata (MQTT 5.0)
    """
    
    topic: str
    payload: Union[bytes, str]
    qos: int
    retain: bool
    dup: bool
    mid: int
    protocol_version: int
    properties: Properties
    
    def __init__(
        self,
        topic: str,
        payload: Optional[Union[bytes, str]] = None,
        qos: int = 0,
        retain: bool = False,
        dup: bool = False,
        mid: int = 0,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Optional[Properties] = None
    ) -> None:
        """
        Create PUBLISH packet.
        
        :param topic: Topic name (must not contain wildcards)
        :param payload: Message payload (string or bytes)
        :param qos: Quality of Service (0=at most once, 1=at least once, 2=exactly once)
        :param retain: Retain message on broker
        :param dup: Duplicate delivery flag
        :param mid: Message identifier for QoS 1/2
        :param protocol_version: MQTT protocol version
        :param properties: Message properties (MQTT 5.0)
        
        Example
        -------
        ```python
            >>> # Simple QoS 0 publish
            >>> packet = PublishPacket(
            ...     topic="sensors/temp",
            ...     payload=b"22.5",
            ...     qos=0
            ... )
            >>> 
            >>> # QoS 1 with string payload
            >>> packet = PublishPacket(
            ...     topic="alerts/high_temp",
            ...     payload="Temperature critical!",
            ...     qos=1,
            ...     mid=123
            ... )
            >>> 
            >>> # Retained message
            >>> packet = PublishPacket(
            ...     topic="devices/status",
            ...     payload=b"online",
            ...     retain=True
            ... )
        ```
        """
    
    def pack(self) -> bytes:
        """
        Serialize PUBLISH packet.
        
        :return: Complete PUBLISH packet as bytes
        
        Example
        -------
        ```python
            >>> packet = PublishPacket("test/topic", b"hello")
            >>> data = packet.pack()
            >>> data[0] >> 4  # Packet type = 3 (PUBLISH)
            3
        ```
        """
    
    @staticmethod
    def unpack(
        flags: int,
        data: bytes,
        protocol_version: int = MQTTProtocolVersion.MQTTv5
    ) -> PublishPacket:
        """
        Deserialize PUBLISH packet from received data.
        
        :param flags: Fixed header flags (contains QoS, DUP, RETAIN)
        :param data: Raw packet data (without fixed header)
        :param protocol_version: MQTT protocol version
        :return: Parsed PUBLISH packet
        
        Example
        -------
        ```python
            >>> # Flags: QoS=1, Retain=1 -> 0x03
            >>> data = b'\\x00\\x04test\\x00\\x01hello'
            >>> packet = PublishPacket.unpack(0x03, data)
            >>> packet.topic
            'test'
            >>> packet.qos
            1
            >>> packet.retain
            True
        ```
        """


class PubackPacket(MQTTPacket):
    """
    MQTT PUBACK packet - acknowledgment for QoS 1 PUBLISH.
    
    Sent in response to a PUBLISH packet with QoS 1, confirming receipt
    of the message. This completes the QoS 1 message delivery handshake.
    
    Attributes:
        mid: Message identifier from corresponding PUBLISH
        reason_code: Acknowledgment result code (MQTT 5.0)
        protocol_version: MQTT protocol version
        properties: Additional metadata (MQTT 5.0)
    """
    
    mid: int
    reason_code: int
    protocol_version: int
    properties: Properties
    
    def __init__(
        self,
        mid: int,
        reason_code: int = ReasonCode.SUCCESS,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Optional[Properties] = None
    ) -> None:
        """
        Create PUBACK packet.
        
        :param mid: Message identifier to acknowledge
        :param reason_code: Success or failure reason
        :param protocol_version: MQTT protocol version
        :param properties: Additional properties (MQTT 5.0)
        
        Example
        -------
        ```python
            >>> # Acknowledge message 123
            >>> packet = PubackPacket(
            ...     mid=123,
            ...     reason_code=ReasonCode.SUCCESS
            ... )
        ```
        """
    
    def pack(self) -> bytes:
        """Serialize PUBACK packet."""
    
    @staticmethod
    def unpack(
        data: bytes,
        protocol_version: int = MQTTProtocolVersion.MQTTv5
    ) -> PubackPacket:
        """
        Deserialize PUBACK packet.
        
        :param data: Raw packet data
        :param protocol_version: MQTT protocol version
        :return: Parsed PUBACK packet
        """


class PubrecPacket(MQTTPacket):
    """
    MQTT PUBREC packet - first response in QoS 2 handshake.
    
    Part of the 4-way QoS 2 handshake. Sent by the receiver in response
    to a PUBLISH with QoS 2, confirming receipt. The sender must respond
    with PUBREL, which is then acknowledged with PUBCOMP.
    
    Attributes:
        packet_id: Message identifier from PUBLISH
        reason_code: Receipt status (MQTT 5.0)
        protocol_version: MQTT protocol version
        properties: Additional metadata (MQTT 5.0)
    """
    
    packet_id: int
    reason_code: int
    protocol_version: int
    properties: Properties
    
    def __init__(
        self,
        packet_id: int,
        reason_code: int = ReasonCode.SUCCESS,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Optional[Properties] = None
    ) -> None:
        """Create PUBREC packet."""
    
    def pack(self) -> bytes:
        """Serialize PUBREC packet."""
    
    @staticmethod
    def unpack(
        data: bytes,
        protocol_version: int = MQTTProtocolVersion.MQTTv5
    ) -> PubrecPacket:
        """Deserialize PUBREC packet."""


class PubrelPacket(MQTTPacket):
    """
    MQTT PUBREL packet - release step in QoS 2 handshake.
    
    Second step in QoS 2 message delivery. Sent by publisher after
    receiving PUBREC, instructing receiver to release the message ID.
    Receiver responds with PUBCOMP to complete the handshake.
    
    Attributes:
        packet_id: Message identifier to release
        reason_code: Release status (MQTT 5.0)
        protocol_version: MQTT protocol version
        properties: Additional metadata (MQTT 5.0)
    """
    
    packet_id: int
    reason_code: int
    protocol_version: int
    properties: Properties
    
    def __init__(
        self,
        packet_id: int,
        reason_code: int = ReasonCode.SUCCESS,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Optional[Properties] = None
    ) -> None:
        """Create PUBREL packet."""
    
    def pack(self) -> bytes:
        """Serialize PUBREL packet."""
    
    @staticmethod
    def unpack(
        data: bytes,
        protocol_version: int = MQTTProtocolVersion.MQTTv5
    ) -> PubrelPacket:
        """Deserialize PUBREL packet."""


class PubcompPacket(MQTTPacket):
    """
    MQTT PUBCOMP packet - final step in QoS 2 handshake.
    
    Completes the QoS 2 message delivery. Sent by the receiver in response
    to PUBREL, confirming that the message ID has been released and the
    exactly-once delivery is complete.
    
    Attributes:
        packet_id: Message identifier being completed
        reason_code: Completion status (MQTT 5.0)
        protocol_version: MQTT protocol version
        properties: Additional metadata (MQTT 5.0)
    """
    
    packet_id: int
    reason_code: int
    protocol_version: int
    properties: Properties
    
    def __init__(
        self,
        packet_id: int,
        reason_code: int = ReasonCode.SUCCESS,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Optional[Properties] = None
    ) -> None:
        """Create PUBCOMP packet."""
    
    def pack(self) -> bytes:
        """Serialize PUBCOMP packet."""
    
    @staticmethod
    def unpack(
        data: bytes,
        protocol_version: int = MQTTProtocolVersion.MQTTv5
    ) -> PubcompPacket:
        """Deserialize PUBCOMP packet."""


class SubscribePacket(MQTTPacket):
    """
    MQTT SUBSCRIBE packet for topic subscriptions.
    
    Requests the broker to send messages matching one or more topic filters
    to the client. Each subscription includes a QoS level indicating the
    maximum QoS the client wishes to receive. Broker responds with SUBACK.
    
    Attributes:
        mid: Message identifier for tracking subscription
        topics: List of (topic, qos) or (topic, qos, options) tuples
        protocol_version: MQTT protocol version
        properties: Subscription properties (MQTT 5.0)
    """
    
    mid: int
    topics: List[Union[Tuple[str, int], Tuple[str, int, int]]]
    protocol_version: int
    properties: Properties
    
    def __init__(
        self,
        mid: int,
        topics: List[Union[Tuple[str, int], Tuple[str, int, int]]],
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Optional[Properties] = None
    ) -> None:
        """
        Create SUBSCRIBE packet.
        
        :param mid: Message identifier
        :param topics: List of subscriptions as (topic, qos) or (topic, qos, options)
        :param protocol_version: MQTT protocol version
        :param properties: Subscription properties (MQTT 5.0)
        
        Example
        -------
        ```python
            >>> # Subscribe to multiple topics
            >>> packet = SubscribePacket(
            ...     mid=1,
            ...     topics=[
            ...         ("sensors/temp", 0),
            ...         ("sensors/humidity", 1),
            ...         ("alerts/#", 2)
            ...     ]
            ... )
            >>> 
            >>> # MQTT 5.0 with subscription options
            >>> packet = SubscribePacket(
            ...     mid=2,
            ...     topics=[
            ...         ("status/+", 1, 0x04)  # No Local option
            ...     ]
            ... )
        ```
        """
    
    def pack(self) -> bytes:
        """
        Serialize SUBSCRIBE packet.
        
        :return: Complete SUBSCRIBE packet as bytes
        """


class SubackPacket(MQTTPacket):
    """
    MQTT SUBACK packet - acknowledgment of subscription.
    
    Broker's response to SUBSCRIBE, confirming each topic subscription
    and indicating the granted QoS level or failure reason for each topic.
    
    Attributes:
        mid: Message identifier from SUBSCRIBE
        return_codes: List of granted QoS levels (MQTT 3.1.1)
        reason_codes: List of subscription results (MQTT 5.0)
        properties: Additional metadata (MQTT 5.0)
    """
    
    mid: int
    return_codes: List[int]
    reason_codes: List[int]
    properties: Properties
    
    def __init__(self) -> None:
        """Create SUBACK packet."""
    
    def pack(self) -> bytes:
        """Serialize SUBACK packet."""
    
    @staticmethod
    def unpack(
        data: bytes,
        protocol_version: int = MQTTProtocolVersion.MQTTv5
    ) -> SubackPacket:
        """
        Deserialize SUBACK packet.
        
        :param data: Raw packet data
        :param protocol_version: MQTT protocol version
        :return: Parsed SUBACK packet
        
        Example
        -------
        ```python
            >>> data = b'\\x00\\x01\\x00\\x01\\x02'  # MID=1, QoS granted: 0,1,2
            >>> packet = SubackPacket.unpack(data)
            >>> packet.reason_codes
            [0, 1, 2]
        ```
        """


class UnsubscribePacket(MQTTPacket):
    """
    MQTT UNSUBSCRIBE packet for removing subscriptions.
    
    Requests the broker to stop sending messages for one or more topic
    filters. Broker responds with UNSUBACK to confirm removal.
    
    Attributes:
        mid: Message identifier
        topics: List of topic filters to unsubscribe from
        protocol_version: MQTT protocol version
        properties: Unsubscribe properties (MQTT 5.0)
    """
    
    mid: int
    topics: List[str]
    protocol_version: int
    properties: Properties
    
    def __init__(
        self,
        mid: int,
        topics: List[str],
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Optional[Properties] = None
    ) -> None:
        """
        Create UNSUBSCRIBE packet.
        
        :param mid: Message identifier
        :param topics: List of topic filters to unsubscribe
        :param protocol_version: MQTT protocol version
        :param properties: Unsubscribe properties (MQTT 5.0)
        
        Example
        -------
        ```python
            >>> packet = UnsubscribePacket(
            ...     mid=1,
            ...     topics=["sensors/temp", "alerts/#"]
            ... )
        ```
        """
    
    def pack(self) -> bytes:
        """Serialize UNSUBSCRIBE packet."""


class UnsubackPacket(MQTTPacket):
    """
    MQTT UNSUBACK packet - acknowledgment of unsubscription.
    
    Broker's response to UNSUBSCRIBE, confirming removal of topic
    subscriptions. For MQTT 5.0, includes reason codes indicating
    success or failure for each topic.
    
    Attributes:
        mid: Message identifier from UNSUBSCRIBE
        reason_codes: List of unsubscribe results (MQTT 5.0)
        properties: Additional metadata (MQTT 5.0)
    """
    
    mid: int
    reason_codes: List[int]
    properties: Properties
    
    def __init__(self) -> None:
        """Create UNSUBACK packet."""
    
    def pack(self) -> bytes:
        """Serialize UNSUBACK packet."""
    
    @staticmethod
    def unpack(
        data: bytes,
        protocol_version: int = MQTTProtocolVersion.MQTTv5
    ) -> UnsubackPacket:
        """Deserialize UNSUBACK packet."""


class PingReqPacket(MQTTPacket):
    """
    MQTT PINGREQ packet - keepalive request.
    
    Sent by client to broker to maintain the connection during periods
    of inactivity. Broker must respond with PINGRESP. If the broker
    doesn't receive a PINGREQ within 1.5x the keepalive interval,
    it will disconnect the client.
    
    This is the simplest MQTT packet - contains only the fixed header.
    """
    
    def __init__(self) -> None:
        """
        Create PINGREQ packet.
        
        Example
        -------
        ```python
            >>> packet = PingReqPacket()
            >>> data = packet.pack()
            >>> len(data)
            2
            >>> data
            b'\\xc0\\x00'
        ```
        """
    
    def pack(self) -> bytes:
        """Serialize PINGREQ packet (2 bytes total)."""


class PingRespPacket(MQTTPacket):
    """
    MQTT PINGRESP packet - keepalive response.
    
    Broker's response to PINGREQ, confirming the connection is alive.
    Like PINGREQ, this is a minimal packet with only the fixed header.
    """
    
    def __init__(self) -> None:
        """Create PINGRESP packet."""
    
    def pack(self) -> bytes:
        """Serialize PINGRESP packet (2 bytes total)."""
    
    @staticmethod
    def unpack() -> PingRespPacket:
        """
        Deserialize PINGRESP packet.
        
        :return: New PingRespPacket instance
        
        Example
        -------
        ```python
            >>> packet = PingRespPacket.unpack()
            >>> isinstance(packet, PingRespPacket)
            True
        ```
        """


class DisconnectPacket(MQTTPacket):
    """
    MQTT DISCONNECT packet - graceful connection termination.
    
    Sent by client or broker to cleanly close the connection. For MQTT 5.0,
    can include a reason code explaining the disconnection and properties
    with additional context (e.g., session expiry interval, reason string).
    
    After sending DISCONNECT, no further packets should be sent on the
    connection except in MQTT 5.0 where broker may send DISCONNECT first.
    
    Attributes:
        reason_code: Disconnection reason (MQTT 5.0)
        protocol_version: MQTT protocol version
        properties: Disconnection properties (MQTT 5.0)
    """
    
    reason_code: int
    protocol_version: int
    properties: Properties
    
    def __init__(
        self,
        reason_code: int = ReasonCode.NORMAL_DISCONNECTION,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Optional[Properties] = None
    ) -> None:
        """
        Create DISCONNECT packet.
        
        :param reason_code: Reason for disconnection
        :param protocol_version: MQTT protocol version
        :param properties: Disconnection properties (MQTT 5.0)
        
        Example
        -------
        ```python
            >>> # Normal disconnection
            >>> packet = DisconnectPacket(
            ...     reason_code=ReasonCode.NORMAL_DISCONNECTION
            ... )
            >>> 
            >>> # Disconnect due to error
            >>> packet = DisconnectPacket(
            ...     reason_code=ReasonCode.UNSPECIFIED_ERROR
            ... )
        ```
        """
    
    def pack(self) -> bytes:
        """Serialize DISCONNECT packet."""
    
    @staticmethod
    def unpack(
        data: bytes,
        protocol_version: int = MQTTProtocolVersion.MQTTv5
    ) -> DisconnectPacket:
        """
        Deserialize DISCONNECT packet.
        
        :param data: Raw packet data
        :param protocol_version: MQTT protocol version
        :return: Parsed DISCONNECT packet
        """
