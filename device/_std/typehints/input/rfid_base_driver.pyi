"""
Common interfaces and memory metadata for contactless RFID drivers.

Example
-------
```python
    >>> from mfrc522 import MFRC522Driver
    >>> driver = MFRC522Driver()
    >>> driver.get_memory_layout()
```
"""


class MemoryLayout:
    """
    Describe the addressable storage units of a supported RFID card.

    :param family: Storage family, such as ``"classic"`` or ``"ntag"``.
    :param name: Human-readable card type.
    :param unit_size: Number of bytes in each storage unit.
    :param unit_count: Number of addressable storage units.
    :param data_units: Unit indices available for user data.

    Example
    -------
    ```python
        >>> data_blocks = tuple(block for block in range(1, 64) if block % 4 != 3)
        >>> layout = MemoryLayout("classic", "MIFARE Classic 1K", 16, 64, data_blocks)
        >>> layout.capacity
        752
    ```
    """

    family: str
    name: str
    unit_size: int
    unit_count: int
    data_units: tuple[int, ...]

    def __init__(
        self,
        family: str,
        name: str,
        unit_size: int,
        unit_count: int,
        data_units: tuple[int, ...],
    ) -> None:
        """
        Create storage metadata for a card layout.

        :param family: Storage family identifier.
        :param name: Human-readable card type.
        :param unit_size: Bytes stored in one unit.
        :param unit_count: Total number of units.
        :param data_units: Unit indices that contain user data.

        Example
        -------
        ```python
            >>> layout = MemoryLayout("ntag", "NTAG213", 4, 45, tuple(range(4, 40)))
            >>> layout.unit_size
            4
        ```
        """
        ...

    @property
    def capacity(self) -> int:
        """
        Get the total number of user-data bytes in this layout.

        :return: Number of bytes across all data units.

        Example
        -------
        ```python
            >>> layout = MemoryLayout("ntag", "NTAG213", 4, 45, tuple(range(4, 40)))
            >>> layout.capacity
            144
        ```
        """
        ...

    def sector(self, unit: int) -> int:
        """
        Get the MIFARE Classic sector containing a storage unit.

        :param unit: Classic block index.
        :return: Sector index.

        :raises ValueError: If the layout is not Classic or the block is invalid.

        Example
        -------
        ```python
            >>> data_blocks = tuple(block for block in range(1, 64) if block % 4 != 3)
            >>> layout = MemoryLayout("classic", "MIFARE Classic 1K", 16, 64, data_blocks)
            >>> layout.sector(5)
            1
        ```
        """
        ...

    @staticmethod
    def is_classic_data_block(block: int) -> bool:
        """
        Check whether a Classic block stores user data rather than sector metadata.

        :param block: Classic block index.
        :return: True for a non-trailer data block.

        Example
        -------
        ```python
            >>> MemoryLayout.is_classic_data_block(4)
            True
            >>> MemoryLayout.is_classic_data_block(7)
            False
        ```
        """
        ...


class RFIDCommunicationError(OSError):
    """Report a failure to communicate with an RFID reader."""


class BaseRFIDDriver:
    """
    Define the common interface implemented by RFID hardware drivers.

    Concrete drivers provide tag selection, authenticated block access, and
    hardware-specific radio-level controls.

    Example
    -------
    ```python
        >>> from mfrc522 import MFRC522Driver
        >>> driver = MFRC522Driver()
        >>> driver.check_connection()
    ```
    """

    LEVEL_0: int
    """Minimum supported receive/transmit level."""
    LEVEL_1: int
    """Second supported receive/transmit level."""
    LEVEL_2: int
    """Middle supported receive/transmit level."""
    LEVEL_3: int
    """Second-highest supported receive/transmit level."""
    LEVEL_4: int
    """Maximum supported receive/transmit level."""

    last_error: str | None
    """Most recent driver error code, or None when no error is recorded."""
    last_uid: list[int] | None
    """UID of the currently selected tag, if any."""
    last_atqa: int | None
    """ATQA value returned when the current tag was selected."""
    last_sak: int | None
    """SAK value returned when the current tag was selected."""

    @property
    def card_type(self) -> str | None:
        """
        Get the selected card's recognized type.

        :return: Card type name, or None when no card is selected.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     print(driver.card_type)
        ```
        """
        ...

    def get_memory_layout(self) -> MemoryLayout | None:
        """
        Get the selected card's supported memory layout.

        :return: Memory metadata, or None if the card is unsupported.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> if driver.connect_tag() is not None:
            ...     layout = driver.get_memory_layout()
        ```
        """
        ...

    def get_data_blocks(self) -> tuple[int, ...] | None:
        """
        Get the selected card's user-data unit indices.

        :return: Data-unit indices, or None if the layout is unavailable.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> if driver.connect_tag() is not None:
            ...     blocks = driver.get_data_blocks()
        ```
        """
        ...

    def _read_tag_version(self) -> bytes | None:
        """
        Read the tag version needed to identify an NTAG memory layout.

        Subclasses implement this hardware-specific operation.

        :return: Eight-byte version response, or None on failure.

        :raises NotImplementedError: If the concrete driver does not implement it.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> if driver.connect_tag() is not None:
            ...     version = driver._read_tag_version()
        ```
        """
        ...

    def read_storage_unit(
        self,
        uid: list[int],
        unit: int,
        key: tuple[int, ...],
        key_type: str,
    ) -> bytes | None:
        """
        Read one unit from Classic or NTAG storage.

        :param uid: UID of the selected card.
        :param unit: Storage-unit index.
        :param key: Six-byte Classic key.
        :param key_type: Classic key type, ``"A"`` or ``"B"``.
        :return: Unit contents, or None when the read fails.

        :raises NotImplementedError: If the concrete driver does not implement it.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     data = driver.read_storage_unit(uid, 4, (255, 255, 255, 255, 255, 255), "A")
            ...     driver.end_session()
        ```
        """
        ...

    def write_storage_unit(
        self,
        uid: list[int],
        unit: int,
        data: bytes,
        key: tuple[int, ...],
        key_type: str,
    ) -> bool:
        """
        Write one user-data unit to Classic or NTAG storage.

        :param uid: UID of the selected card.
        :param unit: Storage-unit index.
        :param data: Exactly one storage unit of bytes.
        :param key: Six-byte Classic key.
        :param key_type: Classic key type, ``"A"`` or ``"B"``.
        :return: True if the write succeeds.

        :raises NotImplementedError: If the concrete driver does not implement it.
        :raises ValueError: If the data length does not match the unit size.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     written = driver.write_storage_unit(
            ...         uid, 4, bytes(16), (255, 255, 255, 255, 255, 255), "A"
            ...     )
            ...     driver.end_session()
        ```
        """
        ...

    def _storage_layout(
        self,
        uid: list[int],
        unit: int,
        write: bool = False,
    ) -> MemoryLayout | None:
        """
        Validate a selected tag and storage-unit access.

        :param uid: UID of the selected card.
        :param unit: Storage-unit index to validate.
        :param write: Whether the unit must be writable.
        :return: Supported layout, or None when access is not valid.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     layout = driver._storage_layout(uid, 4, write=True)
        ```
        """
        ...

    def _validate_classic_access(
        self,
        uid: list[int],
        block: int,
        key: tuple[int, ...],
        key_type: str,
        write: bool = False,
    ) -> bool:
        """
        Validate Classic card identity, block range, and credentials.

        :param uid: UID of the selected card.
        :param block: Classic block index.
        :param key: Six-byte authentication key.
        :param key_type: Key type, either ``"A"`` or ``"B"``.
        :param write: Whether the target block must be user-writable.
        :return: True when the access parameters are valid.

        :raises ValueError: If the key, key type, or UID is malformed.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     allowed = driver._validate_classic_access(
            ...         uid, 4, (255, 255, 255, 255, 255, 255), "A"
            ...     )
        ```
        """
        ...

    @staticmethod
    def crc_a(data: bytes | bytearray | list[int] | tuple[int, ...]) -> bytes:
        """
        Calculate the ISO14443-A CRC for a byte sequence.

        :param data: Bytes to checksum.
        :return: Two-byte CRC in low-byte-first order.

        Example
        -------
        ```python
            >>> crc = BaseRFIDDriver.crc_a(bytes((0x30, 0x04)))
            >>> len(crc)
            2
        ```
        """
        ...

    def init_hardware(self) -> None:
        """
        Initialize the concrete reader hardware and radio settings.

        :raises NotImplementedError: If the concrete driver does not implement it.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> driver.init_hardware()
        ```
        """
        ...

    def check_connection(self) -> None:
        """
        Verify communication with the reader hardware.

        :raises RFIDCommunicationError: If the reader does not respond reliably.
        :raises NotImplementedError: If the concrete driver does not implement it.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> driver.check_connection()
        ```
        """
        ...

    def connect_tag(self) -> list[int] | None:
        """
        Select a nearby ISO14443-A tag and start a session.

        :return: Tag UID, or None when no supported tag is available.

        :raises NotImplementedError: If the concrete driver does not implement it.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     print("Selected UID:", uid)
        ```
        """
        ...

    def read_authenticated_block(
        self,
        uid: list[int],
        block: int,
        key: tuple[int, ...],
        key_type: str,
    ) -> list[int] | None:
        """
        Authenticate and read one 16-byte MIFARE Classic block.

        :param uid: UID of the selected card.
        :param block: Classic block index.
        :param key: Six-byte authentication key.
        :param key_type: Key type, either ``"A"`` or ``"B"``.
        :return: Block bytes as integers, or None when access fails.

        :raises NotImplementedError: If the concrete driver does not implement it.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     block = driver.read_authenticated_block(
            ...         uid, 4, (255, 255, 255, 255, 255, 255), "A"
            ...     )
            ...     driver.end_session()
        ```
        """
        ...

    def write_authenticated_block(
        self,
        uid: list[int],
        block: int,
        data: list[int],
        key: tuple[int, ...],
        key_type: str,
    ) -> bool:
        """
        Authenticate and write one 16-byte MIFARE Classic data block.

        :param uid: UID of the selected card.
        :param block: Classic block index.
        :param data: Exactly 16 data bytes.
        :param key: Six-byte authentication key.
        :param key_type: Key type, either ``"A"`` or ``"B"``.
        :return: True if the block was written.

        :raises NotImplementedError: If the concrete driver does not implement it.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     written = driver.write_authenticated_block(
            ...         uid, 4, [0] * 16, (255, 255, 255, 255, 255, 255), "A"
            ...     )
            ...     driver.end_session()
        ```
        """
        ...

    def end_session(self) -> None:
        """
        Halt the selected tag and release authentication state.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> if driver.connect_tag() is not None:
            ...     driver.end_session()
        ```
        """
        ...

    def is_writable_block(self, block: int) -> bool:
        """
        Check whether a Classic block is a writable data block.

        :param block: Classic block index.
        :return: True when the block is a user-data block in the detected layout.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> driver.is_writable_block(4)
            True
        ```
        """
        ...

    def set_rx_level(self, level: int) -> None:
        """
        Set the receive sensitivity level.

        :param level: Level from ``LEVEL_0`` through ``LEVEL_4``.

        :raises ValueError: If the level is outside the supported range.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> driver.set_rx_level(driver.LEVEL_3)
        ```
        """
        ...

    def get_rx_level(self) -> int:
        """
        Get the current receive sensitivity level.

        :return: Level from ``LEVEL_0`` through ``LEVEL_4``.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> level = driver.get_rx_level()
        ```
        """
        ...

    def set_tx_level(self, level: int) -> None:
        """
        Set the transmit field strength level.

        :param level: Level from ``LEVEL_0`` through ``LEVEL_4``.

        :raises ValueError: If the level is outside the supported range.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> driver.set_tx_level(driver.LEVEL_3)
        ```
        """
        ...

    def get_tx_level(self) -> int:
        """
        Get the current transmit field strength level.

        :return: Level from ``LEVEL_0`` through ``LEVEL_4``.

        Example
        -------
        ```python
            >>> from mfrc522 import MFRC522Driver
            >>> driver = MFRC522Driver()
            >>> level = driver.get_tx_level()
        ```
        """
        ...
