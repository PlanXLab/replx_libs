"""
u-paho-mqtt: MicroPython MQTT 5.0 Client Library

A lightweight, paho-mqtt compatible MQTT client implementation for MicroPython
devices. Supports MQTT 3.1.1 and 5.0 protocols with full QoS 0, 1, and 2 support.

Features:

- Full MQTT 5.0 and 3.1.1 protocol support
- Quality of Service levels 0, 1, and 2 (including exactly-once delivery)
- Async publish with callback-based acknowledgment handling
- MQTT 5.0 Properties system for enhanced metadata
- Reconnection support with configurable retry logic
- TLS/SSL support for secure connections
- Last Will and Testament (LWT) configuration
- Multiple simultaneous subscriptions
- Topic-specific message callbacks
- Memory-efficient implementation for embedded systems
- Comprehensive logging and debugging support

Architecture:

- No threading required (event-based loop)
- Callback-driven event handling
- Minimal memory footprint (~33KB)
- Compatible with RP2040, RP2350, ESP32, ESP8266
- paho-mqtt compatible API for easy migration

QoS Implementation:

- QoS 0: Fire-and-forget (no acknowledgment)
- QoS 1: At-least-once delivery (PUBACK acknowledgment)
- QoS 2: Exactly-once delivery (4-way handshake: PUBREC→PUBREL→PUBCOMP)

Performance:

- Connection: ~659ms average
- QoS 0: 581 messages/second
- QoS 1: 68.7 messages/second (49x faster than umqtt.robust2)
- Async message handling for non-blocking operations
"""
# MCU: {'build': '', 'ver': '1.25.0', 'version': '1.25.0', 'port': 'rp2', 'board': 'RPI_PICO2_W', 'mpy': 'v6.3', 'family': 'micropython', 'cpu': 'RP2350', 'arch': 'armv7emsp'}
# Stubber: v1.24.0

from __future__ import annotations
from typing import Optional, Callable, Any, Dict, Tuple, List, Union

from .client import Client
from .message import MQTTMessage, MQTTMessageInfo
from .enums import MQTTProtocolVersion, QoS, ReasonCode, PacketType, PropertyType, ConnectFlag
from .properties import Properties

__version__: str
__author__: str
__all__: List[str]
