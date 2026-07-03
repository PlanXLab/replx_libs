"""MQTT Message Types

Container objects used by upaho callbacks and publish tracking.

This file mirrors:

- core/_std_comm/src/upaho/message.py

"""

from .properties import Properties


class MQTTMessage:
    """Received MQTT message container.

    Attributes are populated by the upaho Client when a PUBLISH packet is
    received.
    """

    def __init__(self, mid: int = 0, topic: bytes | str = b"") -> None:
        """Create a message container.

        :param mid: Packet identifier
        :param topic: Topic as bytes or str
        :return: None

        Example
        -------
        ```python
            >>> from upaho.message import MQTTMessage
            >>> msg = MQTTMessage(mid=1, topic=b"sensors/temp")
            >>> msg.payload = b"23.5"
            >>> msg.topic
            'sensors/temp'
        ```
        """

    @property
    def topic(self) -> str:
        """Topic as a UTF-8 string.

        Example
        -------
        ```python
            >>> msg.topic
            'sensors/temp'
        ```
        """

    @topic.setter
    def topic(self, value: str | bytes) -> None:
        """Set topic.

        :param value: Topic as str or bytes
        :return: None

        Example
        -------
        ```python
            >>> msg.topic = "sensors/temp"
            >>> msg.topic
            'sensors/temp'
        ```
        """

    @property
    def payload(self) -> bytes:
        """Payload as bytes.

        Example
        -------
        ```python
            >>> msg.payload
            b'23.5'
        ```
        """

    @payload.setter
    def payload(self, value: str | bytes | bytearray | memoryview | None) -> None:
        """Set payload.

        :param value: str (encoded as UTF-8), bytes-like, or None
        :return: None

        Example
        -------
        ```python
            >>> msg.payload = "hello"
            >>> msg.payload
            b'hello'
            >>> msg.payload = None
            >>> msg.payload
            b''
        ```
        """

    @property
    def qos(self) -> int:
        """QoS level.

        Example
        -------
        ```python
            >>> msg.qos
            0
        ```
        """

    @qos.setter
    def qos(self, value: int) -> None:
        """Set QoS.

        :param value: QoS level (0/1/2)
        :return: None

        Example
        -------
        ```python
            >>> msg.qos = 1
            >>> msg.qos
            1
        ```
        """

    @property
    def retain(self) -> bool:
        """Retain flag.

        Example
        -------
        ```python
            >>> msg.retain
            False
        ```
        """

    @retain.setter
    def retain(self, value: bool) -> None:
        """Set retain flag.

        :param value: True if retained
        :return: None

        Example
        -------
        ```python
            >>> msg.retain = True
            >>> msg.retain
            True
        ```
        """

    @property
    def properties(self) -> Properties:
        """MQTT 5.0 properties.

        If no properties were provided, the runtime returns ``Properties.empty()``.

        Example
        -------
        ```python
            >>> props = msg.properties
            >>> props  # doctest: +ELLIPSIS
            Properties(...)
        ```
        """

    @properties.setter
    def properties(self, value: Properties | None) -> None:
        """Set properties.

        :param value: Properties or None
        :return: None

        Example
        -------
        ```python
            >>> from upaho.properties import Properties
            >>> msg.properties = Properties()
        ```
        """

    def __repr__(self) -> str:
        """Return debug representation.

        Example
        -------
        ```python
            >>> repr(msg)  # doctest: +ELLIPSIS
            "MQTTMessage(..."
        ```
        """


class MQTTMessageInfo:
    """Publish tracking object returned by ``Client.publish()``."""

    RC_QUEUED = 0
    RC_PUBLISHED = 1
    RC_CONFIRMED = 2

    def __init__(self, mid: int) -> None:
        """Create a publish tracking object.

        :param mid: Message identifier assigned by the client
        :return: None

        Example
        -------
        ```python
            >>> from upaho.message import MQTTMessageInfo
            >>> info = MQTTMessageInfo(10)
            >>> info.mid
            10
        ```
        """

    @property
    def mid(self) -> int:
        """Message identifier.

        Example
        -------
        ```python
            >>> info.mid
            10
        ```
        """

    @property
    def rc(self) -> int:
        """Internal state code.

        Example
        -------
        ```python
            >>> info.rc
            0
        ```
        """

    def is_published(self) -> bool:
        """Return True if publish is completed.

        Example
        -------
        ```python
            >>> info.is_published()
            False
        ```
        """

    def _set_published(self) -> None:
        """Internal helper used by the client.

        Example
        -------
        ```python
            >>> info._set_published()
            >>> info.is_published()
            True
        ```
        """

    def _set_confirmed(self) -> None:
        """Internal helper used by the client.

        Example
        -------
        ```python
            >>> info._set_confirmed()
            >>> info.rc
            2
        ```
        """

    def __repr__(self) -> str:
        """Return debug representation.

        Example
        -------
        ```python
            >>> repr(info)  # doctest: +ELLIPSIS
            'MQTTMessageInfo(...'
        ```
        """


class SubscriptionInfo:
    """Internal subscription tracking container."""

    def __init__(self, mid: int, topic: str, qos: int) -> None:
        """Create a subscription tracking object.

        :param mid: Message identifier
        :param topic: Topic/pattern
        :param qos: Requested QoS
        :return: None

        Example
        -------
        ```python
            >>> from upaho.message import SubscriptionInfo
            >>> sub = SubscriptionInfo(1, "sensors/#", 0)
            >>> sub.topic
            'sensors/#'
        ```
        """

    @property
    def mid(self) -> int:
        """Message identifier.

        Example
        -------
        ```python
            >>> sub.mid
            1
        ```
        """

    @property
    def topic(self) -> str:
        """Topic/pattern.

        Example
        -------
        ```python
            >>> sub.topic
            'sensors/#'
        ```
        """

    @property
    def qos(self) -> int:
        """Requested QoS.

        Example
        -------
        ```python
            >>> sub.qos
            0
        ```
        """

    @property
    def granted_qos(self) -> object:
        """Granted QoS list or None (implementation-defined).

        Example
        -------
        ```python
            >>> sub.granted_qos is None
            True
        ```
        """

    def _set_granted_qos(self, qos: object) -> None:
        """Internal helper used by the client.

        Example
        -------
        ```python
            >>> sub._set_granted_qos([0])
            >>> sub.granted_qos
            [0]
        ```
        """

    def __repr__(self) -> str:
        """Return debug representation.

        Example
        -------
        ```python
            >>> repr(sub)  # doctest: +ELLIPSIS
            'SubscriptionInfo(...'
        ```
        """
