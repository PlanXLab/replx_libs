"""
High-level RFID operations for Classic and NTAG cards.

Example
-------
```python
    >>> from pn532 import PN532Driver
    >>> reader = RFIDReader(PN532Driver())
    >>> uid = reader.scan_tag_uid()
```
"""

from .rfid_base_driver import BaseRFIDDriver

_Key = tuple[int, ...] | list[int] | bytes | bytearray
_SectorCredentials = tuple[_Key, str] | list[_Key | str]
_SectorKeys = dict[int, _SectorCredentials]


class RFIDReader:
    """
    Provide retrying block, user-memory, and NDEF operations over an RFID driver.

    :param driver: Initialized concrete RFID driver.
    :param max_retries: Maximum attempts for operations that can be retried.
    :param err_reset_threshold: Consecutive hardware errors before reinitialization.

    Example
    -------
    ```python
        >>> from pn532 import PN532Driver
        >>> reader = RFIDReader(PN532Driver(), max_retries=2)
        >>> uid = reader.scan_tag_uid()
    ```
    """

    DEFAULT_KEY: tuple[int, ...]
    """Default MIFARE Classic key (six 0xFF bytes)."""
    NMDEF_KEY: tuple[int, ...]
    """NDEF MIFARE Classic key used by common NFC Forum cards."""
    MAD_KEY: tuple[int, ...]
    """MIFARE Application Directory key."""
    ZERO_KEY: tuple[int, ...]
    """MIFARE Classic key containing six zero bytes."""

    drv: BaseRFIDDriver
    max_retries: int
    last_error: str | None
    """Most recent high-level operation error code."""
    last_failed_unit: int | None
    """Storage-unit index associated with the most recent storage failure."""

    def __init__(
        self,
        driver: BaseRFIDDriver,
        max_retries: int = 2,
        err_reset_threshold: int = 10,
    ) -> None:
        """
        Validate the driver, check its connection, and initialize retry state.

        :param driver: Initialized concrete RFID driver.
        :param max_retries: Maximum attempts for operations that can be retried.
        :param err_reset_threshold: Consecutive hardware errors before reinitialization.

        :raises TypeError: If driver is not a BaseRFIDDriver instance.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> reader = RFIDReader(MFRC522Driver(), max_retries=3)
            >>> reader.last_error
        ```
        """
        ...

    def scan_tag_uid(self) -> list[int] | None:
        """
        Scan for a tag and return its UID.

        :return: Tag UID, or None when no tag is present or a read fails.

        Example
        -------
        ```python
            >>> uid = reader.scan_tag_uid()
            >>> if uid is not None:
            ...     print("Tag UID:", uid)
        ```
        """
        ...

    def read_data_block(
        self,
        block: int,
        key: _Key = DEFAULT_KEY,
        key_type: str = "A",
    ) -> list[int] | None:
        """
        Read one authenticated 16-byte MIFARE Classic block.

        :param block: Classic block index.
        :param key: Six-byte authentication key.
        :param key_type: Key type, either ``"A"`` or ``"B"``.
        :return: Block data as integers, or None when the read fails.

        Example
        -------
        ```python
            >>> block = reader.read_data_block(4)
            >>> if block is not None:
            ...     print(bytes(block))
        ```
        """
        ...

    def write_data_block(
        self,
        block: int,
        payload_16bytes: bytes | bytearray | list[int],
        key: _Key = DEFAULT_KEY,
        key_type: str = "A",
        verify: bool = True,
    ) -> bool:
        """
        Write one user data block, optionally verifying it by reading it back.

        :param block: Classic block index.
        :param payload_16bytes: Exactly sixteen bytes to write.
        :param key: Six-byte authentication key.
        :param key_type: Key type, either ``"A"`` or ``"B"``.
        :param verify: Read the block back and compare the written bytes.
        :return: True if the write, and optional verification, succeeds.

        :raises ValueError: If the block is protected or payload length is not 16.

        Example
        -------
        ```python
            >>> payload = bytes(range(16))
            >>> written = reader.write_data_block(4, payload, verify=True)
            >>> print("Write verified:", written)
        ```
        """
        ...

    def get_user_capacity(self) -> int | None:
        """
        Get Classic structural user-data capacity.

        Capacity does not guarantee that the current sector keys permit access.

        :return: User-data capacity in bytes, or None for an unsupported card.

        Example
        -------
        ```python
            >>> capacity = reader.get_user_capacity()
            >>> if capacity is not None:
            ...     print("Classic data bytes:", capacity)
        ```
        """
        ...

    def read_user_data(
        self,
        address: int,
        length: int,
        key: _Key = DEFAULT_KEY,
        key_type: str = "A",
        sector_keys: _SectorKeys | None = None,
    ) -> bytes | None:
        """
        Read a byte range from the Classic card's virtual user-data area.

        :param address: Byte offset in the user-data area.
        :param length: Number of bytes to read.
        :param key: Default six-byte key for sectors without an override.
        :param key_type: Default key type, either ``"A"`` or ``"B"``.
        :param sector_keys: Optional per-sector ``(key, key_type)`` overrides.
        :return: Requested bytes, or None when a card or block read fails.

        :raises ValueError: If the range, credentials, or capacity is invalid.

        Example
        -------
        ```python
            >>> header = reader.read_user_data(address=0, length=8)
            >>> if header is not None:
            ...     print(header.hex())
        ```
        """
        ...

    def write_user_data(
        self,
        address: int,
        data: bytes | bytearray | memoryview,
        key: _Key = DEFAULT_KEY,
        key_type: str = "A",
        verify: bool = True,
        sector_keys: _SectorKeys | None = None,
    ) -> bool:
        """
        Write a byte range to the Classic card's virtual user-data area.

        A failed multi-unit write may leave an already-written prefix on the card.

        :param address: Byte offset in the user-data area.
        :param data: Bytes to write.
        :param key: Default six-byte key for sectors without an override.
        :param key_type: Default key type, either ``"A"`` or ``"B"``.
        :param verify: Read back each written unit and compare it with the input.
        :param sector_keys: Optional per-sector ``(key, key_type)`` overrides.
        :return: True if every required unit is written and verified.

        :raises TypeError: If data is not bytes-like.
        :raises ValueError: If the range, credentials, or capacity is invalid.

        Example
        -------
        ```python
            >>> payload = b"sensor-01"
            >>> if reader.write_user_data(0, payload):
            ...     print("User data stored")
        ```
        """
        ...

    def get_ndef_capacity(self) -> int | None:
        """
        Get the maximum NDEF message size supported by the selected NTAG.

        :return: Message capacity in bytes, or None when unavailable.

        Example
        -------
        ```python
            >>> capacity = reader.get_ndef_capacity()
            >>> if capacity is not None:
            ...     print("NDEF bytes available:", capacity)
        ```
        """
        ...

    def read_ndef(self) -> bytes | None:
        """
        Read and validate the NDEF message stored on an NTAG.

        :return: Encoded NDEF message, or None when it is missing or unreadable.

        Example
        -------
        ```python
            >>> message = reader.read_ndef()
            >>> if message is not None:
            ...     print("NDEF length:", len(message))
        ```
        """
        ...

    def write_ndef(
        self,
        message: bytes | bytearray | memoryview,
        verify: bool = True,
    ) -> bool:
        """
        Write an encoded NDEF message to an NTAG.

        The TLV length is committed after payload pages have been written.

        :param message: Complete encoded NDEF message.
        :param verify: Read back each written storage unit for comparison.
        :return: True if the NDEF message is written successfully.

        :raises TypeError: If message is not bytes-like.
        :raises ValueError: If the message is malformed or does not fit.

        Example
        -------
        ```python
            >>> from rfid_ndef import encode_uri
            >>> message = encode_uri("https://example.com")
            >>> reader.write_ndef(message, verify=True)
        ```
        """
        ...

    def read_uri(self) -> str | None:
        """
        Read the first URI record from the selected NTAG.

        :return: URI string, or None when no URI can be read.

        Example
        -------
        ```python
            >>> uri = reader.read_uri()
            >>> if uri is not None:
            ...     print(uri)
        ```
        """
        ...

    def write_uri(self, uri: str, verify: bool = True) -> bool:
        """
        Encode and write one URI record to an NTAG.

        :param uri: URI with a valid scheme.
        :param verify: Read back written units and verify their contents.
        :return: True if the URI record is written successfully.

        :raises ValueError: If the URI is invalid or does not fit on the tag.

        Example
        -------
        ```python
            >>> reader.write_uri("https://example.com/device", verify=True)
        ```
        """
        ...

    def pack_16bytes(self, text: str) -> bytes:
        """
        Encode text as a UTF-8 field padded or truncated to sixteen bytes.

        :param text: Text to encode.
        :return: Exactly sixteen bytes.

        Example
        -------
        ```python
            >>> field = reader.pack_16bytes("sensor-01")
            >>> len(field)
            16
        ```
        """
        ...

    def unpack_16bytes(self, data_list: list[int] | bytes | bytearray) -> str:
        """
        Decode a padded 16-byte text field as UTF-8.

        :param data_list: Block bytes as integers or a bytes-like sequence.
        :return: Decoded text with trailing zero padding removed.

        Example
        -------
        ```python
            >>> field = reader.pack_16bytes("sensor-01")
            >>> reader.unpack_16bytes(field)
            'sensor-01'
        ```
        """
        ...
