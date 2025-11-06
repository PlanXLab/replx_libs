"""
u-paho-mqtt: MicroPython MQTT 5.0 Client Library

A lightweight, paho-mqtt compatible MQTT client for MicroPython with MQTT 5.0 support.

Features:
- MQTT 5.0 and 3.1.1 protocol support
- paho-mqtt inspired API for easy migration
- No threading dependency (manual loop control)
- Memory optimized for embedded systems
- TLS/SSL encryption support
- Full QoS 0, 1, and 2 support (Exactly Once delivery)
- Topic wildcards (+ and #)
- Last Will and Testament (LWT)
- MQTT 5.0 properties

Example:
    >>> from upaho import Client
    >>> 
    >>> def on_connect(client, userdata, flags, rc, properties):
    ...     print(f"Connected with result code {rc}")
    ...     client.subscribe("sensor/#", qos=1)
    >>> 
    >>> def on_message(client, userdata, msg):
    ...     print(f"{msg.topic}: {msg.payload}")
    >>> 
    >>> client = Client(client_id="device001")
    >>> client.username_pw_set("user", "password")
    >>> client.on_connect = on_connect
    >>> client.on_message = on_message
    >>> 
    >>> client.connect("mqtt.example.com", 1883, 60)
    >>> client.loop_forever()

Author: PlanXLab Development Team
License: MIT
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"

# Core client
from .client import Client

# Message classes
from .message import MQTTMessage, MQTTMessageInfo

# Enums and constants
from .enums import (
    MQTTProtocolVersion,
    QoS,
    ReasonCode,
    ConnectReturnCode,
    PacketType,
    PropertyType,
    reason_code_to_string
)

# Properties
from .properties import Properties

# Public API
__all__ = [
    # Main client
    'Client',
    
    # Message classes
    'MQTTMessage',
    'MQTTMessageInfo',
    
    # Protocol versions
    'MQTTProtocolVersion',
    
    # QoS levels
    'QoS',
    
    # Reason codes
    'ReasonCode',
    'ConnectReturnCode',
    'reason_code_to_string',
    
    # Properties
    'Properties',
    'PropertyType',
    
    # Packet types (advanced users)
    'PacketType',
    
    # Version
    '__version__',
    '__author__',
]


# Convenience aliases (paho-mqtt compatibility)
MQTT_ERR_SUCCESS = ReasonCode.SUCCESS
MQTT_ERR_PROTOCOL = ReasonCode.PROTOCOL_ERROR
MQTT_ERR_NO_CONN = ReasonCode.NOT_AUTHORIZED
MQTT_ERR_CONN_REFUSED = ReasonCode.NOT_AUTHORIZED

# Protocol version aliases
MQTTv311 = MQTTProtocolVersion.MQTTv311
MQTTv5 = MQTTProtocolVersion.MQTTv5
