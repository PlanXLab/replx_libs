"""MQTT Packet Types

Internal packet encoder/decoder types used by the upaho client.

This file mirrors:

- core/_std_comm/src/upaho/packets.py

"""

import micropython

from .enums import MQTTProtocolVersion, ReasonCode
from .properties import Properties


class MQTTPacket:
    """Base class for MQTT packets."""

    packet_type: int
    flags: int

    def __init__(self, packet_type: int, flags: int = 0) -> None:
        """Create a packet container.

        :param packet_type: Packet type (upper nibble) value
        :param flags: Fixed header flags (lower nibble)
        :return: None

        Example
        -------
        ```python
            >>> pkt = MQTTPacket(0xC0)
        ```
        """

    def pack(self) -> bytes:
        """Serialize packet into MQTT wire format.

        :return: Packed bytes
        :raises NotImplementedError: Base class method

        Example
        -------
        ```python
            >>> pkt.pack()
            Traceback (most recent call last):
            ...
        ```
        """

    def _pack_fixed_header(self, remaining_length: int) -> bytes:
        """Pack fixed header.

        :param remaining_length: Remaining length value
        :return: Fixed header bytes

        Example
        -------
        ```python
            >>> hdr = pkt._pack_fixed_header(0)
            >>> isinstance(hdr, (bytes, bytearray))
            True
        ```
        """


class ConnectPacket(MQTTPacket):
    """CONNECT packet."""

    def __init__(
        self,
        client_id: str,
        clean_start: bool = True,
        keepalive: int = 60,
        username: str | None = None,
        password: str | None = None,
        will_topic: str | None = None,
        will_payload: str | bytes | None = None,
        will_qos: int = 0,
        will_retain: bool = False,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Properties | None = None,
        will_properties: Properties | None = None,
    ) -> None:
        """Create CONNECT packet.

        Example
        -------
        ```python
            >>> from upaho.packets import ConnectPacket
            >>> pkt = ConnectPacket(client_id="dev001")
            >>> data = pkt.pack()
        ```
        """

    def pack(self) -> bytes:
        """Serialize CONNECT packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
            >>> isinstance(data, (bytes, bytearray))
            True
        ```
        """


class ConnackPacket(MQTTPacket):
    """CONNACK packet."""

    session_present: bool
    reason_code: int
    properties: Properties

    def __init__(self) -> None:
        """Create empty CONNACK container.

        Example
        -------
        ```python
            >>> from upaho.packets import ConnackPacket
            >>> pkt = ConnackPacket()
        ```
        """

    def unpack(data: bytes) -> "ConnackPacket":
        """Decode CONNACK from bytes.

        :param data: Packet bytes
        :return: ConnackPacket instance

        Example
        -------
        ```python
            >>> # Typically used internally after receiving CONNACK
            >>> pkt = ConnackPacket.unpack(data)
        ```
        """


class PublishPacket(MQTTPacket):
    """PUBLISH packet."""

    topic: str
    payload: bytes
    qos: int
    retain: bool
    dup: bool
    mid: int | None
    properties: Properties

    def __init__(
        self,
        topic: str,
        payload: str | bytes | None = None,
        qos: int = 0,
        retain: bool = False,
        dup: bool = False,
        mid: int | None = None,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Properties | None = None,
    ) -> None:
        """Create PUBLISH packet.

        Example
        -------
        ```python
            >>> from upaho.packets import PublishPacket
            >>> pkt = PublishPacket("sensors/temp", payload=b"23.5", qos=0)
            >>> data = pkt.pack()
        ```
        """

    def pack(self) -> bytes:
        """Serialize PUBLISH packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
        ```
        """

    def unpack(flags: int, data: bytes, protocol_version: int = MQTTProtocolVersion.MQTTv5) -> "PublishPacket":
        """Decode PUBLISH from bytes.

        :param flags: Fixed header flags
        :param data: Remaining packet bytes
        :param protocol_version: Protocol version
        :return: PublishPacket instance

        Example
        -------
        ```python
            >>> pkt2 = PublishPacket.unpack(flags, data)
            >>> pkt2.topic
            'sensors/temp'
        ```
        """


class PubackPacket(MQTTPacket):
    """PUBACK packet."""

    mid: int
    reason_code: int
    properties: Properties

    def __init__(
        self,
        mid: int,
        reason_code: int = ReasonCode.SUCCESS,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Properties | None = None,
    ) -> None:
        """Create PUBACK packet.

        Example
        -------
        ```python
            >>> from upaho.packets import PubackPacket
            >>> pkt = PubackPacket(mid=1)
        ```
        """

    def pack(self) -> bytes:
        """Serialize PUBACK packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
        ```
        """

    def unpack(data: bytes, protocol_version: int = MQTTProtocolVersion.MQTTv5) -> "PubackPacket":
        """Decode PUBACK from bytes.

        Example
        -------
        ```python
            >>> pkt2 = PubackPacket.unpack(data)
        ```
        """


class PubrecPacket(MQTTPacket):
    """PUBREC packet."""

    packet_id: int
    reason_code: int
    properties: Properties

    def __init__(
        self,
        packet_id: int,
        reason_code: int = ReasonCode.SUCCESS,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Properties | None = None,
    ) -> None:
        """Create PUBREC packet.

        Example
        -------
        ```python
            >>> from upaho.packets import PubrecPacket
            >>> pkt = PubrecPacket(packet_id=1)
        ```
        """

    def pack(self) -> bytes:
        """Serialize PUBREC packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
        ```
        """

    def unpack(data: bytes, protocol_version: int = MQTTProtocolVersion.MQTTv5) -> "PubrecPacket":
        """Decode PUBREC from bytes.

        Example
        -------
        ```python
            >>> pkt2 = PubrecPacket.unpack(data)
        ```
        """


class PubrelPacket(MQTTPacket):
    """PUBREL packet."""

    packet_id: int
    reason_code: int
    properties: Properties

    def __init__(
        self,
        packet_id: int,
        reason_code: int = ReasonCode.SUCCESS,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Properties | None = None,
    ) -> None:
        """Create PUBREL packet.

        Example
        -------
        ```python
            >>> from upaho.packets import PubrelPacket
            >>> pkt = PubrelPacket(packet_id=1)
        ```
        """

    def pack(self) -> bytes:
        """Serialize PUBREL packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
        ```
        """

    def unpack(data: bytes, protocol_version: int = MQTTProtocolVersion.MQTTv5) -> "PubrelPacket":
        """Decode PUBREL from bytes.

        Example
        -------
        ```python
            >>> pkt2 = PubrelPacket.unpack(data)
        ```
        """


class PubcompPacket(MQTTPacket):
    """PUBCOMP packet."""

    packet_id: int
    reason_code: int
    properties: Properties

    def __init__(
        self,
        packet_id: int,
        reason_code: int = ReasonCode.SUCCESS,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Properties | None = None,
    ) -> None:
        """Create PUBCOMP packet.

        Example
        -------
        ```python
            >>> from upaho.packets import PubcompPacket
            >>> pkt = PubcompPacket(packet_id=1)
        ```
        """

    def pack(self) -> bytes:
        """Serialize PUBCOMP packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
        ```
        """

    def unpack(data: bytes, protocol_version: int = MQTTProtocolVersion.MQTTv5) -> "PubcompPacket":
        """Decode PUBCOMP from bytes.

        Example
        -------
        ```python
            >>> pkt2 = PubcompPacket.unpack(data)
        ```
        """


class SubscribePacket(MQTTPacket):
    """SUBSCRIBE packet."""

    mid: int
    topics: list[tuple[str, int]]
    properties: Properties

    def __init__(
        self,
        mid: int,
        topics: list[tuple[str, int]],
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Properties | None = None,
    ) -> None:
        """Create SUBSCRIBE packet.

        Example
        -------
        ```python
            >>> from upaho.packets import SubscribePacket
            >>> pkt = SubscribePacket(mid=1, topics=[("sensors/#", 0)])
            >>> data = pkt.pack()
        ```
        """

    def pack(self) -> bytes:
        """Serialize SUBSCRIBE packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
        ```
        """


class SubackPacket(MQTTPacket):
    """SUBACK packet."""

    mid: int
    return_codes: list[int]
    properties: Properties

    def __init__(self) -> None:
        """Create empty SUBACK container.

        Example
        -------
        ```python
            >>> from upaho.packets import SubackPacket
            >>> pkt = SubackPacket()
        ```
        """

    def unpack(data: bytes, protocol_version: int = MQTTProtocolVersion.MQTTv5) -> "SubackPacket":
        """Decode SUBACK from bytes.

        Example
        -------
        ```python
            >>> pkt2 = SubackPacket.unpack(data)
        ```
        """


class UnsubscribePacket(MQTTPacket):
    """UNSUBSCRIBE packet."""

    mid: int
    topics: list[str]
    properties: Properties

    def __init__(
        self,
        mid: int,
        topics: list[str],
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Properties | None = None,
    ) -> None:
        """Create UNSUBSCRIBE packet.

        Example
        -------
        ```python
            >>> from upaho.packets import UnsubscribePacket
            >>> pkt = UnsubscribePacket(mid=1, topics=["sensors/#"])
            >>> data = pkt.pack()
        ```
        """

    def pack(self) -> bytes:
        """Serialize UNSUBSCRIBE packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
        ```
        """


class UnsubackPacket(MQTTPacket):
    """UNSUBACK packet."""

    mid: int
    reason_codes: list[int]
    properties: Properties

    def __init__(self) -> None:
        """Create empty UNSUBACK container.

        Example
        -------
        ```python
            >>> from upaho.packets import UnsubackPacket
            >>> pkt = UnsubackPacket()
        ```
        """

    def unpack(data: bytes, protocol_version: int = MQTTProtocolVersion.MQTTv5) -> "UnsubackPacket":
        """Decode UNSUBACK from bytes.

        Example
        -------
        ```python
            >>> pkt2 = UnsubackPacket.unpack(data)
        ```
        """


class PingReqPacket(MQTTPacket):
    """PINGREQ packet."""

    def __init__(self) -> None:
        """Create PINGREQ packet.

        Example
        -------
        ```python
            >>> from upaho.packets import PingReqPacket
            >>> pkt = PingReqPacket()
        ```
        """

    def pack(self) -> bytes:
        """Serialize PINGREQ packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
        ```
        """


class PingRespPacket(MQTTPacket):
    """PINGRESP packet."""

    def __init__(self) -> None:
        """Create empty PINGRESP container.

        Example
        -------
        ```python
            >>> from upaho.packets import PingRespPacket
            >>> pkt = PingRespPacket()
        ```
        """

    def unpack() -> "PingRespPacket":
        """Create PINGRESP instance.

        Example
        -------
        ```python
            >>> pkt = PingRespPacket.unpack()
        ```
        """


class DisconnectPacket(MQTTPacket):
    """DISCONNECT packet."""

    reason_code: int
    properties: Properties

    def __init__(
        self,
        reason_code: int = ReasonCode.NORMAL_DISCONNECTION,
        protocol_version: int = MQTTProtocolVersion.MQTTv5,
        properties: Properties | None = None,
    ) -> None:
        """Create DISCONNECT packet.

        Example
        -------
        ```python
            >>> from upaho.packets import DisconnectPacket
            >>> pkt = DisconnectPacket()
        ```
        """

    def pack(self) -> bytes:
        """Serialize DISCONNECT packet.

        Example
        -------
        ```python
            >>> data = pkt.pack()
        ```
        """

    def unpack(data: bytes, protocol_version: int = MQTTProtocolVersion.MQTTv5) -> "DisconnectPacket":
        """Decode DISCONNECT from bytes.

        Example
        -------
        ```python
            >>> pkt2 = DisconnectPacket.unpack(data)
        ```
        """
