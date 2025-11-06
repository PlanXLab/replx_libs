from __future__ import annotations
from typing import Optional
from .properties import Properties

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class MQTTMessage:
    """
    Received MQTT message with topic, payload, and metadata.
    
    This class represents a message received from the MQTT broker through
    a subscription. It contains all relevant information about the message
    including topic, payload, QoS level, retain flag, and MQTT 5.0 properties.
    
    Attributes:
    
        - topic: The topic the message was published to
        - payload: Message content as bytes
        - qos: Quality of Service level (0, 1, or 2)
        - retain: Whether this is a retained message
        - mid: Message identifier (for QoS > 0)
        - properties: MQTT 5.0 properties (if available)
    """
    
    topic: str
    payload: bytes
    qos: int
    retain: bool
    mid: int
    properties: Optional[Properties]
    
    def __init__(
        self,
        topic: str = "",
        payload: bytes = b"",
        qos: int = 0,
        retain: bool = False,
        mid: int = 0,
        properties: Optional[Properties] = None
    ) -> None:
        """
        Initialize a received MQTT message.
        
        Creates a new MQTTMessage instance with the specified parameters.
        This is typically done automatically by the MQTT client when a
        message is received, but can be manually created for testing.
        
        :param topic: Message topic
        :param payload: Message payload as bytes
        :param qos: Quality of Service level (0, 1, or 2)
        :param retain: Retain flag
        :param mid: Message identifier
        :param properties: MQTT 5.0 properties
        
        Example
        -------
        ```python
            >>> # Typically received in on_message callback
            >>> def on_message(client, userdata, msg):
            ...     print(f"Topic: {msg.topic}")
            ...     print(f"Payload: {msg.payload.decode()}")
            ...     print(f"QoS: {msg.qos}")
            ...     if msg.retain:
            ...         print("This is a retained message")
        ```
        """

class MQTTMessageInfo:
    """
    Published message tracking information.
    
    This class tracks the delivery status of a published message with QoS > 0.
    It allows checking whether the message has been acknowledged by the broker
    and waiting for acknowledgment to complete.
    
    For QoS levels:
    - QoS 0: Immediately marked as published
    - QoS 1: Published after PUBACK received
    - QoS 2: Published after PUBCOMP received (4-way handshake complete)
    
    Attributes:
    
        - mid: Message identifier
        - rc: Result code (0 = success)
    """
    
    mid: int
    rc: int
    
    def __init__(self, mid: int) -> None:
        """
        Initialize message tracking information.
        
        Creates a new tracking object for a published message. This is
        done automatically by the MQTT client when publish() is called.
        
        :param mid: Message identifier assigned by client
        
        Example
        -------
        ```python
            >>> # Returned by publish()
            >>> info = client.publish("sensors/temp", "23.5", qos=1)
            >>> print(f"Message ID: {info.mid}")
        ```
        """
    
    def is_published(self) -> bool:
        """
        Check if the message has been acknowledged by the broker.
        
        Returns True if the publish operation is complete (acknowledgment
        received for QoS > 0, or immediately for QoS 0).
        
        :return: True if published, False if still pending
        
        Example
        -------
        ```python
            >>> info = client.publish("data", payload, qos=1)
            >>> while not info.is_published():
            ...     client.loop(timeout=0.1)
            >>> print("Message published")
        ```
        """

class SubscriptionInfo:
    """
    Subscription information for internal tracking.
    
    This class stores information about active subscriptions, including
    the topic pattern and requested QoS level.
    
    Attributes:
    
        - topic: Subscribed topic pattern (may include wildcards)
        - qos: Requested Quality of Service level
    """
    
    topic: str
    qos: int
    
    def __init__(self, topic: str, qos: int = 0) -> None:
        """
        Initialize subscription information.
        
        Creates a new subscription info object. This is used internally
        by the MQTT client to track active subscriptions.
        
        :param topic: Topic pattern (may include + and # wildcards)
        :param qos: Quality of Service level (0, 1, or 2)
        
        Example
        -------
        ```python
            >>> # Created internally when subscribe() is called
            >>> client.subscribe("sensors/+/temperature", qos=1)
        ```
        """
