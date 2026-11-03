"""
I2C driver for PN532 RFID readers.

Example
-------
```python
    >>> from pn532 import PN532Driver
    >>> driver = PN532Driver()
    >>> driver.check_connection()
```
"""

from .rfid_base_driver import BaseRFIDDriver


class PN532Driver(BaseRFIDDriver):
    """
    Read and write ISO14443-A tags using a PN532 over I2C.

    :param i2c_bus: Machine I2C peripheral number.
    :param scl: I2C clock GPIO pin.
    :param sda: I2C data GPIO pin.
    :param addr: PN532 I2C address.
    :param rst: Optional reset GPIO pin.
    :param irq: Optional active-low interrupt GPIO pin.
    :param freq: I2C bus frequency in hertz.

    Example
    -------
    ```python
        >>> driver = PN532Driver(i2c_bus=0, scl=22, sda=21, addr=0x24)
        >>> driver.check_connection()
    ```
    """

    def __init__(
        self,
        i2c_bus: int = 0,
        scl: int = 22,
        sda: int = 21,
        addr: int = 0x24,
        rst: int | None = None,
        irq: int | None = None,
        freq: int = 400000,
    ) -> None:
        """
        Configure I2C and initialize the PN532 reader.

        :param i2c_bus: Machine I2C peripheral number.
        :param scl: I2C clock GPIO pin.
        :param sda: I2C data GPIO pin.
        :param addr: PN532 I2C address.
        :param rst: Optional reset GPIO pin.
        :param irq: Optional active-low interrupt GPIO pin.
        :param freq: I2C bus frequency in hertz.

        Example
        -------
        ```python
            >>> driver = PN532Driver(i2c_bus=0, scl=22, sda=21, freq=400000)
            >>> driver.get_rx_level()
        ```
        """
        ...

    def init_hardware(self) -> None:
        """
        Reset the reader when configured and apply its communication settings.

        Example
        -------
        ```python
            >>> driver = PN532Driver()
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
            >>> driver = PN532Driver()
            >>> driver.set_rx_level(driver.LEVEL_3)
        ```
        """
        ...

    def get_rx_level(self) -> int:
        """
        Get the configured receive sensitivity level.

        :return: Level from ``LEVEL_0`` through ``LEVEL_4``.

        Example
        -------
        ```python
            >>> driver = PN532Driver()
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
            >>> driver = PN532Driver()
            >>> driver.set_tx_level(driver.LEVEL_3)
        ```
        """
        ...

    def get_tx_level(self) -> int:
        """
        Get the configured transmit field strength level.

        :return: Level from ``LEVEL_0`` through ``LEVEL_4``.

        Example
        -------
        ```python
            >>> driver = PN532Driver()
            >>> tx_level = driver.get_tx_level()
        ```
        """
        ...

    def check_connection(self) -> None:
        """
        Verify that the PN532 returns a valid firmware-version response.

        :raises RFIDCommunicationError: If the firmware response is invalid.

        Example
        -------
        ```python
            >>> driver = PN532Driver()
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
            >>> driver = PN532Driver()
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
            >>> driver = PN532Driver()
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
        :param data: Block data; the first sixteen values are sent.
        :param key: Six-byte authentication key.
        :param key_type: Authentication key type, ``"A"`` or ``"B"``.
        :return: True if the block was written successfully.

        Example
        -------
        ```python
            >>> driver = PN532Driver()
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
        Release the selected PN532 target and clear authentication state.

        Example
        -------
        ```python
            >>> driver = PN532Driver()
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
            >>> driver = PN532Driver()
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
            >>> driver = PN532Driver()
            >>> uid = driver.connect_tag()
            >>> if uid is not None:
            ...     ok = driver.write_storage_unit(
            ...         uid, 4, bytes(16), (255, 255, 255, 255, 255, 255), "A"
            ...     )
            ...     driver.end_session()
        ```
        """
        ...
