"""MQTT 5.0 Properties Container

Properties are key/value metadata attached to MQTT 5.0 packets.

Implementation notes:

- The upaho implementation stores properties by integer property id
  (see ``upaho.enums.PropertyType``).
- ``PropertyType.USER_PROPERTY`` is stored as a list of ``(key, value)`` pairs.
- ``unpack()`` returns ``(props, new_offset)`` because the wire format is read
  from an existing packet buffer.

"""

import micropython


class Properties:
    """Container for MQTT properties."""

    _EMPTY = None
    _EMPTY_PACKED = b"\x00"

    @classmethod
    def empty(cls) -> "Properties":
        """Return a singleton empty Properties instance.

        :return: Empty properties object (treat as read-only)

        Example
        -------
        ```python
            >>> from upaho.properties import Properties
            >>> Properties.empty()  # doctest: +ELLIPSIS
            Properties(...)
        ```
        """

    def __init__(self) -> None:
        """Create an empty Properties container.

        Example
        -------
        ```python
            >>> from upaho.properties import Properties
            >>> props = Properties()
        ```
        """

    def set(self, property_id: int, value: object) -> None:
        """Set a property value.

        :param property_id: Integer property id (typically from ``PropertyType``)
        :param value: Property value
        :return: None

        Example
        -------
        ```python
            >>> from upaho.properties import Properties
            >>> from upaho.enums import PropertyType
            >>> props = Properties()
            >>> props.set(PropertyType.CONTENT_TYPE, "application/json")
        ```
        """

    def get(self, property_id: int, default: object = None) -> object:
        """Get a property value.

        :param property_id: Integer property id
        :param default: Default value if the property is missing
        :return: Stored value or default

        Example
        -------
        ```python
            >>> from upaho.enums import PropertyType
            >>> props.get(PropertyType.CONTENT_TYPE)
            'application/json'
            >>> props.get(999, "missing")
            'missing'
        ```
        """

    def has(self, property_id: int) -> bool:
        """Check if a property exists.

        :param property_id: Integer property id
        :return: True if present

        Example
        -------
        ```python
            >>> from upaho.enums import PropertyType
            >>> props.has(PropertyType.CONTENT_TYPE)
            True
        ```
        """

    def remove(self, property_id: int) -> None:
        """Remove a property.

        :param property_id: Integer property id
        :return: None

        Example
        -------
        ```python
            >>> from upaho.enums import PropertyType
            >>> props.remove(PropertyType.CONTENT_TYPE)
            >>> props.has(PropertyType.CONTENT_TYPE)
            False
        ```
        """

    def clear(self) -> None:
        """Remove all properties.

        Example
        -------
        ```python
            >>> props.clear()
        ```
        """

    def pack(self) -> bytes:
        """Serialize properties into MQTT wire format.

        :return: Wire format bytes (length varint + properties payload)

        Example
        -------
        ```python
            >>> data = props.pack()
            >>> isinstance(data, (bytes, bytearray))
            True
        ```
        """

    @staticmethod
    def unpack(data: bytes, offset: int = 0) -> tuple["Properties", int]:
        """Deserialize properties from MQTT wire format.

        :param data: Packet buffer
        :param offset: Start offset in buffer
        :return: (Properties, new_offset)
        :raises ValueError: If the data is malformed

        Example
        -------
        ```python
            >>> props2, off = Properties.unpack(props.pack(), 0)
            >>> isinstance(off, int)
            True
        ```
        """

    def __repr__(self) -> str:
        """Return debug representation.

        Example
        -------
        ```python
            >>> repr(props)  # doctest: +ELLIPSIS
            'Properties(...'
        ```
        """
