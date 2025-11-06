"""
Module: 'upaho.properties' on micropython-v1.25.0-rp2-RPI_PICO2_W

MQTT 5.0 Properties Handler
"""
# MCU: {'build': '', 'ver': '1.25.0', 'version': '1.25.0', 'port': 'rp2', 'board': 'RPI_PICO2_W', 'mpy': 'v6.3', 'family': 'micropython', 'cpu': 'RP2350', 'arch': 'armv7emsp'}
# Stubber: v1.24.0

from __future__ import annotations
from typing import Optional, Any, Dict, List, Tuple

class Properties:
    """
    MQTT 5.0 properties container for enhanced message metadata.
    
    This class provides a convenient interface for working with MQTT 5.0
    properties, which allow attaching additional metadata to MQTT packets.
    Properties can specify content types, message expiry, user-defined
    key-value pairs, and many other enhanced features.
    
    Common Properties:
    
        - Content-Type: MIME type of payload (e.g., "application/json")
        - Message-Expiry-Interval: Time in seconds before message expires
        - Response-Topic: Topic for response messages
        - Correlation-Data: Request-response correlation identifier
        - User-Property: Custom key-value pairs for application data
        - Topic-Alias: Integer alias for topic string (bandwidth optimization)
    
    Property Types:
    
        MQTT 5.0 defines 40+ property types for various use cases:
        - Message properties: Content-Type, Expiry, Format Indicator
        - Request-Response: Response-Topic, Correlation-Data
        - Connection: Session-Expiry-Interval, Keepalive, Receive-Maximum
        - Authentication: Authentication-Method, Authentication-Data
        - Topic management: Topic-Alias, Topic-Alias-Maximum
        - User-defined: User-Property (can have multiple instances)
    
    Usage Pattern:
    
        1. Create a Properties instance
        2. Set desired properties using set()
        3. Pass to publish(), subscribe(), connect(), etc.
        4. Receive properties in callbacks from broker
        5. Query properties using get() or has()
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize MQTT 5.0 properties container.
        
        Creates a new properties object, optionally initialized with a
        dictionary of property names and values. Property names can be
        either the string name (e.g., "Content-Type") or the integer
        property identifier.
        
        :param data: Initial properties as dictionary (optional)
        
        Example
        -------
        ```python
            >>> # Empty properties
            >>> props = Properties()
            >>> 
            >>> # Pre-initialized properties
            >>> props = Properties({
            ...     "Content-Type": "application/json",
            ...     "Message-Expiry-Interval": 3600
            ... })
        ```
        """
    
    def set(self, name: str, value: Any) -> None:
        """
        Set a property value by name.
        
        Sets the specified property to the given value. The property name
        should be the standard MQTT 5.0 property name (e.g., "Content-Type").
        For User-Property, you can set multiple values by calling set()
        multiple times or passing a tuple of (key, value).
        
        :param name: Property name (standard MQTT 5.0 name)
        :param value: Property value (type depends on property)
        
        Supported Properties:
        
            - Content-Type: str
            - Message-Expiry-Interval: int (seconds)
            - Response-Topic: str
            - Correlation-Data: bytes
            - User-Property: Tuple[str, str] or List[Tuple[str, str]]
            - Topic-Alias: int
            - Payload-Format-Indicator: int (0=bytes, 1=UTF-8)
            - Subscription-Identifier: int
        
        Example
        -------
        ```python
            >>> props = Properties()
            >>> props.set("Content-Type", "application/json")
            >>> props.set("Message-Expiry-Interval", 3600)
            >>> 
            >>> # User properties (custom key-value pairs)
            >>> props.set("User-Property", ("device-id", "sensor001"))
            >>> props.set("User-Property", ("location", "warehouse"))
            >>> 
            >>> # Use in publish
            >>> client.publish("data", payload, qos=1, properties=props)
        ```
        """
    
    def get(self, name: str, default: Any = None) -> Any:
        """
        Get a property value by name.
        
        Retrieves the value of the specified property. If the property
        is not set, returns the default value. For User-Property, returns
        a list of all (key, value) tuples.
        
        :param name: Property name (standard MQTT 5.0 name)
        :param default: Default value if property not found
        
        :return: Property value or default
        
        Example
        -------
        ```python
            >>> # In on_message callback
            >>> def on_message(client, userdata, msg):
            ...     if msg.properties:
            ...         content_type = msg.properties.get("Content-Type")
            ...         if content_type == "application/json":
            ...             data = json.loads(msg.payload)
            ...         
            ...         # Get user properties
            ...         user_props = msg.properties.get("User-Property", [])
            ...         for key, value in user_props:
            ...             print(f"{key}: {value}")
        ```
        """
    
    def has(self, name: str) -> bool:
        """
        Check if a property is set.
        
        Returns True if the specified property exists in this container,
        False otherwise. Useful for checking optional properties before
        attempting to retrieve them.
        
        :param name: Property name to check
        
        :return: True if property exists, False otherwise
        
        Example
        -------
        ```python
            >>> if msg.properties and msg.properties.has("Content-Type"):
            ...     content_type = msg.properties.get("Content-Type")
            ...     print(f"Content type: {content_type}")
        ```
        """
    
    def pack(self) -> bytes:
        """
        Serialize properties to MQTT wire format.
        
        Encodes all properties into a byte string suitable for transmission
        in an MQTT packet. This is called automatically by the MQTT client
        when sending packets with properties.
        
        :return: Serialized properties as bytes
        
        Example
        -------
        ```python
            >>> props = Properties()
            >>> props.set("Content-Type", "text/plain")
            >>> wire_format = props.pack()
            >>> # wire_format can be sent in MQTT packet
        ```
        """
    
    @staticmethod
    def unpack(data: bytes) -> Properties:
        """
        Deserialize properties from MQTT wire format.
        
        Decodes a byte string (from an MQTT packet) into a Properties
        object. This is called automatically by the MQTT client when
        receiving packets with properties.
        
        :param data: Serialized properties bytes from MQTT packet
        
        :return: Properties object with decoded values
        
        :raises ValueError: If data format is invalid
        
        Example
        -------
        ```python
            >>> # Typically used internally by client
            >>> props = Properties.unpack(packet_bytes)
            >>> content_type = props.get("Content-Type")
        ```
        """
    
    def __repr__(self) -> str:
        """
        Get string representation of properties.
        
        Returns a human-readable string showing all properties and their
        values. Useful for debugging and logging.
        
        :return: String representation
        
        Example
        -------
        ```python
            >>> props = Properties()
            >>> props.set("Content-Type", "application/json")
            >>> print(props)
            Properties({'Content-Type': 'application/json'})
        ```
        """
