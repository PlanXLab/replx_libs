"""upaho - MQTT Client Package

MicroPython MQTT client package with a paho-like API.

This package is designed for embedded MicroPython environments and exposes a
small set of public symbols via ``__all__``.

Features:

- MQTT 3.1.1 and MQTT 5.0 (implementation-defined subset)
- QoS 0/1/2 publish/subscribe
- TLS (CA/cert/key) and TLS verification toggle
- Last Will and Testament (LWT) and retained messages
- Topic specific message callbacks
- MQTT 5.0 Properties container

Public API:

- Client
- MQTTMessage / MQTTMessageInfo
- Properties
- Enums/constants and helper: MQTTProtocolVersion, QoS, ReasonCode,
  ConnectReturnCode, PacketType, PropertyType, reason_code_to_string

"""

from .client import Client
from .enums import (
    ConnectReturnCode,
    MQTTProtocolVersion,
    PacketType,
    PropertyType,
    QoS,
    ReasonCode,
    reason_code_to_string,
)
from .message import MQTTMessage, MQTTMessageInfo
from .properties import Properties

__all__ = [
    "Client",
    "MQTTMessage",
    "MQTTMessageInfo",
    "MQTTProtocolVersion",
    "QoS",
    "ReasonCode",
    "ConnectReturnCode",
    "reason_code_to_string",
    "Properties",
    "PropertyType",
    "PacketType",
]
