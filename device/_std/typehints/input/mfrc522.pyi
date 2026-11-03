"""
SPI driver for MFRC522 RFID readers.

Example
-------
```python
    >>> from mfrc522 import MFRC522Driver
    >>> driver = MFRC522Driver()
    >>> driver.check_connection()
```
"""

from .rfid_base_driver import BaseRFIDDriver


class MFRC522Driver(BaseRFIDDriver):
    """
    Read and write ISO14443-A tags using an MFRC522 over SPI.

    :param spi_bus: Machine SPI peripheral number.
    :param sck: SPI clock GPIO pin.
    :param mosi: SPI controller-output GPIO pin.
    :param miso: SPI controller-input GPIO pin.
    :param cs: Reader chip-select GPIO pin.
    :param baudrate: SPI clock rate in hertz.

    Example
    -------
    ```python
        >>> driver = MFRC522Driver(spi_bus=1, sck=14, mosi=13, miso=12, cs=15)
        >>> driver.check_connection()
    ```
    """

    def __init__(
        self,
        spi_bus: int = 1,
        sck: int = 14,
        mosi: int = 13,
        miso: int = 12,
        cs: int = 15,
        baudrate: int = 1000000,
    ) -> None:
        """
        Configure SPI and initialize the MFRC522 reader.

        :param spi_bus: Machine SPI peripheral number.
        :param sck: SPI clock GPIO pin.
        :param mosi: SPI controller-output GPIO pin.
        :param miso: SPI controller-input GPIO pin.
        :param cs: Reader chip-select GPIO pin.
        :param baudrate: SPI clock rate in hertz.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver(spi_bus=1, cs=15, baudrate=1000000)
            >>> driver.get_version()
        ```
        """
        ...

    def init_hardware(self) -> None:
        """
        Reset the reader and initialize timer, antenna, and RF settings.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> driver.init_hardware()
        ```
        """
        ...

    def set_rx_level(self, level: int) -> None:
        """
        Set the receive sensitivity level.

        :param level: Level from ``LEVEL_0`` through ``LEVEL_4``.

        :raises ValueError: If level is not an integer in the supported range.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> driver.set_rx_level(driver.LEVEL_3)
        ```
        """
        ...

    def get_rx_level(self) -> int:
        """
        Get the receive sensitivity level currently configured in the reader.

        :return: Matching level, or ``LEVEL_2`` if the register value is unknown.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> rx_level = driver.get_rx_level()
        ```
        """
        ...

    def set_tx_level(self, level: int) -> None:
        """
        Set the transmit field strength level.

        :param level: Level from ``LEVEL_0`` through ``LEVEL_4``.

        :raises ValueError: If level is not an integer in the supported range.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> driver.set_tx_level(driver.LEVEL_3)
        ```
        """
        ...

    def get_tx_level(self) -> int:
        """
        Get the transmit field strength level currently configured in the reader.

        :return: Matching level, or ``LEVEL_2`` if the register values are unknown.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> tx_level = driver.get_tx_level()
        ```
        """
        ...

    def get_version(self) -> int:
        """
        Read the MFRC522 version register.

        :return: Raw value of the reader's VersionReg.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> version = driver.get_version()
            >>> print("MFRC522 version:", hex(version))
        ```
        """
        ...

    def check_connection(self) -> None:
        """
        Verify that the MFRC522 returns a stable, nonempty version value.

        :raises RFIDCommunicationError: If SPI communication fails.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> driver.check_connection()
        ```
        """
        ...

    def connect_tag(self) -> list[int] | None:
        """
        Select an ISO14443-A tag and establish a reader session.

        :return: UID as a list of bytes, or None when no tag is found.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     print("Tag UID:", uid)
            ...     driver.end_session()
        ```
        """
        ...

    def read_authenticated_block(
        self,
        uid: list[int],
        block: int,
        key: tuple[int, ...],
        key_type: str = "A",
    ) -> list[int] | None:
        """
        Authenticate and read a MIFARE Classic block.

        :param uid: UID of the selected card.
        :param block: Classic block index.
        :param key: Six-byte authentication key.
        :param key_type: Authentication key type, ``"A"`` or ``"B"``.
        :return: Sixteen block bytes, or None if authentication or reading fails.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     data = driver.read_authenticated_block(
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
        key_type: str = "A",
    ) -> bool:
        """
        Authenticate and write a MIFARE Classic data block.

        :param uid: UID of the selected card.
        :param block: Classic block index.
        :param data: Block data; the first sixteen values are written.
        :param key: Six-byte authentication key.
        :param key_type: Authentication key type, ``"A"`` or ``"B"``.
        :return: True if the block was written successfully.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     ok = driver.write_authenticated_block(
            ...         uid, 4, [0] * 16, (255, 255, 255, 255, 255, 255), "A"
            ...     )
            ...     driver.end_session()
        ```
        """
        ...

    def end_session(self) -> None:
        """
        Halt the selected tag and clear Crypto1 authentication state.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> if driver.connect_tag() is not None:
            ...     driver.end_session()
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
        Read a Classic block or four-byte NTAG page as a storage unit.

        :param uid: UID of the selected card.
        :param unit: Block or page index.
        :param key: Six-byte Classic key; unused for NTAG pages.
        :param key_type: Classic authentication key type, ``"A"`` or ``"B"``.
        :return: Unit contents, or None when reading fails.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     contents = driver.read_storage_unit(
            ...         uid, 4, (255, 255, 255, 255, 255, 255), "A"
            ...     )
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
        Write one Classic block or one four-byte NTAG page.

        :param uid: UID of the selected card.
        :param unit: Block or page index.
        :param data: Exactly one storage unit of bytes.
        :param key: Six-byte Classic key; unused for NTAG pages.
        :param key_type: Classic authentication key type, ``"A"`` or ``"B"``.
        :return: True if the unit was written.

        :raises ValueError: If data length differs from the storage-unit size.

        Example
        -------
        ```python
            >>> driver = MFRC522Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     ok = driver.write_storage_unit(
            ...         uid, 4, bytes(16), (255, 255, 255, 255, 255, 255), "A"
            ...     )
            ...     driver.end_session()
        ```
        """
        ...
