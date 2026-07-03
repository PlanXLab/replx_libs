"""MQTT Constants and Helpers

Constants used by the upaho MQTT implementation.

This file mirrors the implementation values in:

- core/_std_comm/src/upaho/enums.py

"""


class MQTTProtocolVersion:
    """MQTT protocol version constants."""

    MQTTv311 = 4
    MQTTv5 = 5


class QoS:
    """Quality of Service level constants."""

    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2


class PacketType:
    """MQTT packet type constants (fixed header high nibble)."""

    CONNECT = 0x10
    CONNACK = 0x20
    PUBLISH = 0x30
    PUBACK = 0x40
    PUBREC = 0x50
    PUBREL = 0x60
    PUBCOMP = 0x70
    SUBSCRIBE = 0x80
    SUBACK = 0x90
    UNSUBSCRIBE = 0xA0
    UNSUBACK = 0xB0
    PINGREQ = 0xC0
    PINGRESP = 0xD0
    DISCONNECT = 0xE0
    AUTH = 0xF0


class ReasonCode:
    """MQTT reason code constants (MQTT 5.0 style)."""

    SUCCESS = 0x00
    NORMAL_DISCONNECTION = 0x00
    GRANTED_QOS_0 = 0x00
    GRANTED_QOS_1 = 0x01
    GRANTED_QOS_2 = 0x02
    DISCONNECT_WITH_WILL_MESSAGE = 0x04
    NO_MATCHING_SUBSCRIBERS = 0x10
    NO_SUBSCRIPTION_EXISTED = 0x11
    CONTINUE_AUTHENTICATION = 0x18
    RE_AUTHENTICATE = 0x19

    UNSPECIFIED_ERROR = 0x80
    MALFORMED_PACKET = 0x81
    PROTOCOL_ERROR = 0x82
    IMPLEMENTATION_SPECIFIC_ERROR = 0x83
    UNSUPPORTED_PROTOCOL_VERSION = 0x84
    CLIENT_IDENTIFIER_NOT_VALID = 0x85
    BAD_USER_NAME_OR_PASSWORD = 0x86
    NOT_AUTHORIZED = 0x87
    SERVER_UNAVAILABLE = 0x88
    SERVER_BUSY = 0x89
    BANNED = 0x8A
    SERVER_SHUTTING_DOWN = 0x8B
    BAD_AUTHENTICATION_METHOD = 0x8C
    KEEPALIVE_TIMEOUT = 0x8D
    SESSION_TAKEN_OVER = 0x8E
    TOPIC_FILTER_INVALID = 0x8F
    TOPIC_NAME_INVALID = 0x90
    PACKET_IDENTIFIER_IN_USE = 0x91
    PACKET_IDENTIFIER_NOT_FOUND = 0x92
    RECEIVE_MAXIMUM_EXCEEDED = 0x93
    TOPIC_ALIAS_INVALID = 0x94
    PACKET_TOO_LARGE = 0x95
    MESSAGE_RATE_TOO_HIGH = 0x96
    QUOTA_EXCEEDED = 0x97
    ADMINISTRATIVE_ACTION = 0x98
    PAYLOAD_FORMAT_INVALID = 0x99
    RETAIN_NOT_SUPPORTED = 0x9A
    QOS_NOT_SUPPORTED = 0x9B
    USE_ANOTHER_SERVER = 0x9C
    SERVER_MOVED = 0x9D
    SHARED_SUBSCRIPTIONS_NOT_SUPPORTED = 0x9E
    CONNECTION_RATE_EXCEEDED = 0x9F
    MAXIMUM_CONNECT_TIME = 0xA0
    SUBSCRIPTION_IDENTIFIERS_NOT_SUPPORTED = 0xA1
    WILDCARD_SUBSCRIPTIONS_NOT_SUPPORTED = 0xA2

    NETWORK_ERROR = 0xFF


class PropertyType:
    """MQTT 5.0 property identifier constants."""

    PAYLOAD_FORMAT_INDICATOR = 0x01
    MESSAGE_EXPIRY_INTERVAL = 0x02
    CONTENT_TYPE = 0x03
    RESPONSE_TOPIC = 0x08
    CORRELATION_DATA = 0x09
    SUBSCRIPTION_IDENTIFIER = 0x0B
    SESSION_EXPIRY_INTERVAL = 0x11
    ASSIGNED_CLIENT_IDENTIFIER = 0x12
    SERVER_KEEP_ALIVE = 0x13
    AUTHENTICATION_METHOD = 0x15
    AUTHENTICATION_DATA = 0x16
    REQUEST_PROBLEM_INFORMATION = 0x17
    WILL_DELAY_INTERVAL = 0x18
    REQUEST_RESPONSE_INFORMATION = 0x19
    RESPONSE_INFORMATION = 0x1A
    SERVER_REFERENCE = 0x1C
    REASON_STRING = 0x1F
    RECEIVE_MAXIMUM = 0x21
    TOPIC_ALIAS_MAXIMUM = 0x22
    TOPIC_ALIAS = 0x23
    MAXIMUM_QOS = 0x24
    RETAIN_AVAILABLE = 0x25
    USER_PROPERTY = 0x26
    MAXIMUM_PACKET_SIZE = 0x27
    WILDCARD_SUBSCRIPTION_AVAILABLE = 0x28
    SUBSCRIPTION_IDENTIFIER_AVAILABLE = 0x29
    SHARED_SUBSCRIPTION_AVAILABLE = 0x2A


class SubscriptionOption:
    """SUBSCRIBE options bitmask constants."""

    QOS_MASK = 0x03
    NO_LOCAL = 0x04
    RETAIN_AS_PUBLISHED = 0x08
    RETAIN_HANDLING_MASK = 0x30

    SEND_RETAINED = 0x00
    SEND_RETAINED_IF_NEW = 0x10
    DO_NOT_SEND_RETAINED = 0x20


class ConnectFlag:
    """CONNECT packet flag constants."""

    CLEAN_SESSION = 0x02
    CLEAN_START = 0x02
    WILL_FLAG = 0x04
    WILL_QOS_0 = 0x00
    WILL_QOS_1 = 0x08
    WILL_QOS_2 = 0x10
    WILL_RETAIN = 0x20
    PASSWORD = 0x40
    USERNAME = 0x80


class ConnectReturnCode:
    """MQTT 3.1.1 CONNACK return codes."""

    ACCEPTED = 0x00
    REFUSED_PROTOCOL_VERSION = 0x01
    REFUSED_IDENTIFIER_REJECTED = 0x02
    REFUSED_SERVER_UNAVAILABLE = 0x03
    REFUSED_BAD_USERNAME_PASSWORD = 0x04
    REFUSED_NOT_AUTHORIZED = 0x05


PROPERTY_DATA_TYPE: dict[int, str]


def reason_code_to_string(code: int) -> str:
    """Convert a reason code integer to a readable string.

    :param code: MQTT reason code integer
    :return: Human readable label (or an "Unknown (...)" string)

    Example
    -------
    ```python
        >>> from upaho.enums import ReasonCode, reason_code_to_string
        >>> reason_code_to_string(ReasonCode.SUCCESS)
        'Success'
    ```
    """
