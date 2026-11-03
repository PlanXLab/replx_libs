"""
Helpers for encoding NDEF records and Type 2 Tag memory.

Example
-------
```python
    >>> message = encode_uri("https://example.com")
    >>> decode_uri(message)
    'https://example.com'
```
"""


class NdefRecord:
    """
    Represent one NDEF record.

    :param tnf: Type Name Format value from 0 through 5.
    :param record_type: Record type bytes.
    :param payload: Record payload bytes.
    :param identifier: Optional record identifier bytes.

    Example
    -------
    ```python
        >>> record = NdefRecord(1, b"U", b"\x04example.com")
        >>> record.record_type
        b'U'
    ```
    """

    tnf: int
    """NDEF Type Name Format value."""
    record_type: bytes
    """Record type field."""
    payload: bytes
    """Record payload field."""
    identifier: bytes
    """Optional record identifier."""

    def __init__(
        self,
        tnf: int,
        record_type: bytes,
        payload: bytes,
        identifier: bytes = b"",
    ) -> None:
        """
        Initialize an NDEF record after validating its type and field lengths.

        :param tnf: Type Name Format value from 0 through 5.
        :param record_type: Record type bytes.
        :param payload: Record payload bytes.
        :param identifier: Optional record identifier bytes.

        :raises ValueError: If the TNF or record fields are invalid.

        Example
        -------
        ```python
            >>> text_record = NdefRecord(1, b"T", b"\x02enHello")
            >>> text_record.tnf
            1
        ```
        """
        ...


def encode_message(records: list[NdefRecord]) -> bytes:
    """
    Serialize records into one NDEF message.

    :param records: NDEF records in message order.
    :return: Encoded NDEF message bytes.

    Example
    -------
    ```python
        >>> record = NdefRecord(1, b"U", b"\x04example.com")
        >>> message = encode_message([record])
        >>> message[0] & 0xC0
        192
    ```
    """
    ...


def decode_message(message: bytes) -> list[NdefRecord]:
    """
    Parse a serialized NDEF message into records.

    :param message: Encoded NDEF message bytes.
    :return: Records in message order.

    :raises ValueError: If the message is truncated, chunked, or malformed.

    Example
    -------
    ```python
        >>> encoded = encode_uri("https://example.com")
        >>> records = decode_message(encoded)
        >>> records[0].record_type
        b'U'
    ```
    """
    ...


def encode_uri(uri: str) -> bytes:
    """
    Encode a URI as an NFC Forum well-known URI record.

    :param uri: URI with a valid scheme.
    :return: One-record NDEF message containing the URI.

    :raises ValueError: If the URI has no valid scheme or contains control/space characters.

    Example
    -------
    ```python
        >>> message = encode_uri("https://example.com/device")
        >>> decode_uri(message)
        'https://example.com/device'
    ```
    """
    ...


def decode_uri(message: bytes) -> str | None:
    """
    Extract the first URI record from an NDEF message.

    :param message: Encoded NDEF message bytes.
    :return: Decoded URI, or None when no URI record is present.

    :raises ValueError: If the message, URI prefix, or decoded URI is invalid.

    Example
    -------
    ```python
        >>> message = encode_uri("https://example.com")
        >>> uri = decode_uri(message)
        >>> print(uri)
        https://example.com
    ```
    """
    ...


def parse_cc(cc: bytes, physical_capacity: int) -> tuple[int, bool]:
    """
    Validate a Type 2 Capability Container.

    :param cc: Four-byte Capability Container.
    :param physical_capacity: Available tag memory in bytes.
    :return: Advertised data capacity and whether the tag is writable.

    :raises ValueError: If the container is malformed or advertises inaccessible memory.

    Example
    -------
    ```python
        >>> capacity, writable = parse_cc(bytes((0xE1, 0x10, 0x12, 0x00)), 144)
        >>> capacity, writable
        (144, True)
    ```
    """
    ...


class Type2Memory:
    """
    Parse and update the Type 2 Tag TLV area containing an NDEF message.

    :param data: User memory bytes read from the tag.

    Example
    -------
    ```python
        >>> area = Type2Memory(bytes(64))
        >>> updated, header = area.replace(encode_uri("https://example.com"))
        >>> len(updated)
        64
    ```
    """

    data: bytes
    """Raw Type 2 memory image."""
    mapping: list[int]
    """Physical byte offsets corresponding to the parsed logical area."""
    start: int
    """Logical position where the NDEF TLV starts or can be appended."""
    limit: int
    """Logical end of the available NDEF TLV region."""
    message: bytes | None
    """Existing NDEF message payload, or None when no NDEF TLV exists."""

    def __init__(self, data: bytes) -> None:
        """
        Parse control and NDEF TLVs from a Type 2 memory image.

        :param data: User memory bytes read from the tag.

        :raises ValueError: If a TLV or control area is truncated or invalid.

        Example
        -------
        ```python
            >>> area = Type2Memory(bytes(128))
            >>> area.message is None
            True
        ```
        """
        ...

    @property
    def capacity(self) -> int:
        """
        Get the maximum NDEF message size supported by the available TLV region.

        :return: Maximum encoded message length, excluding TLV overhead.

        Example
        -------
        ```python
            >>> area = Type2Memory(bytes(128))
            >>> area.capacity
            126
        ```
        """
        ...

    def replace(self, message: bytes) -> tuple[bytes, tuple[int, ...]]:
        """
        Build an updated memory image containing the supplied NDEF message.

        :param message: Complete, encoded NDEF message.
        :return: Updated memory bytes and the physical offsets of the TLV header.

        :raises ValueError: If the message is invalid or does not fit in the TLV region.

        Example
        -------
        ```python
            >>> area = Type2Memory(bytes(128))
            >>> message = encode_uri("https://example.com")
            >>> updated, header = area.replace(message)
            >>> len(header) >= 2
            True
        ```
        """
        ...
