"""MQTT Client

MicroPython MQTT client with a paho-like API.

This stub mirrors the implementation in:

- core/_std_comm/src/upaho/client.py

Typical usage:

1. Create Client
2. Set callbacks (on_connect, on_message, ...)
3. Configure auth/TLS/LWT
4. connect()
5. subscribe()/publish()
6. loop() periodically (or loop_forever())

"""

import micropython

from .enums import MQTTProtocolVersion
from .message import MQTTMessage, MQTTMessageInfo
from .properties import Properties


class Client:
    """MQTT client."""

    on_connect: object | None
    on_disconnect: object | None
    on_message: object | None
    on_publish: object | None
    on_publish_failed: object | None
    on_subscribe: object | None
    on_unsubscribe: object | None
    on_log: object | None

    def __init__(
        self,
        client_id: str = "",
        clean_session: bool | None = None,
        userdata: object = None,
        protocol: int = MQTTProtocolVersion.MQTTv5,
        transport: str = "tcp",
    ) -> None:
        """Create a client instance.

        :param client_id: Client identifier ("" for auto)
        :param clean_session: Clean session / clean start flag
        :param userdata: User object passed to callbacks
        :param protocol: MQTTProtocolVersion.MQTTv5 or MQTTProtocolVersion.MQTTv311
        :param transport: Only "tcp" is supported
        :return: None

        Example
        -------
        ```python
            >>> from upaho.client import Client
            >>> client = Client("device001")
        ```
        """

    def username_pw_set(self, username: str, password: str | None = None) -> None:
        """Set broker authentication credentials.

        :param username: Username
        :param password: Password (optional)
        :return: None

        Example
        -------
        ```python
            >>> client.username_pw_set("user", "pass")
        ```
        """

    def tls_set(self, ca_certs: str | None = None, certfile: str | None = None, keyfile: str | None = None) -> None:
        """Configure TLS parameters.

        :param ca_certs: CA certificate path
        :param certfile: Client certificate path
        :param keyfile: Client private key path
        :return: None

        Example
        -------
        ```python
            >>> client.tls_set(ca_certs="/flash/ca.crt")
            >>> client.connect("mqtt.example.com", 8883)
        ```
        """

    def tls_insecure_set(self, value: bool) -> None:
        """Enable/disable server certificate verification.

        :param value: True disables verification (insecure)
        :return: None

        Example
        -------
        ```python
            >>> client.tls_set(ca_certs="/flash/ca.crt")
            >>> client.tls_insecure_set(False)
        ```
        """

    def will_set(
        self,
        topic: str,
        payload: str | bytes | None = None,
        qos: int = 0,
        retain: bool = False,
        properties: Properties | None = None,
    ) -> None:
        """Set Last Will and Testament (LWT).

        :param topic: Will topic
        :param payload: Will payload
        :param qos: Will QoS
        :param retain: Will retain flag
        :param properties: MQTT 5.0 properties (used only in MQTTv5)
        :return: None

        Example
        -------
        ```python
            >>> client.will_set("device/status", "offline", qos=1, retain=True)
        ```
        """

    def will_clear(self) -> None:
        """Clear previously set LWT.

        Example
        -------
        ```python
            >>> client.will_clear()
        ```
        """

    def max_inflight_messages_set(self, inflight: int) -> None:
        """Limit maximum inflight QoS1/QoS2 messages.

        :param inflight: Maximum inflight count
        :return: None

        Example
        -------
        ```python
            >>> client.max_inflight_messages_set(20)
        ```
        """

    def user_data_set(self, userdata: object) -> None:
        """Update userdata passed to callbacks.

        :param userdata: New userdata object
        :return: None

        Example
        -------
        ```python
            >>> client.user_data_set({"device": "sensor001"})
        ```
        """

    def connect(self, host: str, port: int = 1883, keepalive: int = 60) -> int:
        """Connect to a broker.

        :param host: Broker host or IP
        :param port: Broker port
        :param keepalive: Keepalive seconds
        :return: Reason code integer (0 for success)

        Example
        -------
        ```python
            >>> rc = client.connect("test.mosquitto.org", 1883, 60)
            >>> rc
            0
        ```
        """

    def reconnect(self) -> int:
        """Reconnect using the last connect() parameters.

        :return: Reason code integer

        Example
        -------
        ```python
            >>> rc = client.reconnect()
        ```
        """

    def disconnect(self, reasoncode: int | None = None, properties: Properties | None = None) -> int:
        """Disconnect from broker.

        :param reasoncode: MQTT 5.0 reason code (optional)
        :param properties: MQTT 5.0 properties (optional)
        :return: Reason code integer

        Example
        -------
        ```python
            >>> client.disconnect()
            0
        ```
        """

    def publish(
        self,
        topic: str,
        payload: str | bytes | None = None,
        qos: int = 0,
        retain: bool = False,
        properties: Properties | None = None,
    ) -> MQTTMessageInfo:
        """Publish a message.

        :param topic: Topic to publish to
        :param payload: Payload (str/bytes/None)
        :param qos: QoS level
        :param retain: Retain flag
        :param properties: MQTT 5.0 properties (optional)
        :return: MQTTMessageInfo for tracking

        Example
        -------
        ```python
            >>> info = client.publish("sensors/temp", "23.5", qos=1)
            >>> while not info.is_published():
            ...     client.loop(timeout=0.1)
        ```
        """

    def subscribe(
        self,
        topic: str | tuple[str, int] | list[tuple[str, int]],
        qos: int = 0,
        properties: Properties | None = None,
    ) -> tuple[int, int | None]:
        """Subscribe to topics.

        :param topic: Topic string, (topic, qos) tuple, or list of tuples
        :param qos: Default QoS when topic is a string
        :param properties: MQTT 5.0 properties (optional)
        :return: (reason_code, mid) where mid may be None on failure

        Example
        -------
        ```python
            >>> rc, mid = client.subscribe("sensors/#", qos=0)
        ```
        """

    def unsubscribe(self, topic: str | list[str], properties: Properties | None = None) -> tuple[int, int | None]:
        """Unsubscribe from topics.

        :param topic: Topic string or list of topics
        :param properties: MQTT 5.0 properties (optional)
        :return: (reason_code, mid) where mid may be None on failure

        Example
        -------
        ```python
            >>> rc, mid = client.unsubscribe("sensors/#")
        ```
        """

    def message_callback_add(self, sub: str, callback: object) -> None:
        """Register a per-topic callback.

        Callback signature at runtime:
            callback(client, userdata, message)

        :param sub: Topic pattern (wildcards +/# supported)
        :param callback: Callable
        :return: None

        Example
        -------
        ```python
            >>> def cb(client, userdata, msg):
            ...     print(msg.topic)
            >>> client.message_callback_add("sensors/#", cb)
        ```
        """

    def message_callback_remove(self, sub: str) -> None:
        """Remove a per-topic callback.

        :param sub: Topic pattern
        :return: None

        Example
        -------
        ```python
            >>> client.message_callback_remove("sensors/#")
        ```
        """

    def loop(self, timeout: float = 1.0, max_packets: int = 1) -> int:
        """Process network traffic once.

        :param timeout: Poll timeout seconds
        :param max_packets: Maximum packets to process (implementation-defined)
        :return: Reason code integer

        Example
        -------
        ```python
            >>> client.loop(timeout=0.1)
            0
        ```
        """

    def loop_forever(self, timeout: float = 1.0, max_packets: int = 1, retry_first_connection: bool = False) -> None:
        """Run loop() continuously.

        :param timeout: Poll timeout per iteration
        :param max_packets: Maximum packets per iteration
        :param retry_first_connection: Retry initial connection until connected
        :return: None

        Example
        -------
        ```python
            >>> client.loop_forever()  # blocks
        ```
        """

    def is_connected(self) -> bool:
        """Return True if currently connected.

        Example
        -------
        ```python
            >>> client.is_connected()
            True
        ```
        """
