"""
SPI Master and SPI Slave for RP2350 (ticle)

Provides an industrial-grade SPI Master wrapper and a PIO+DMA based
SPI Mode 0 Slave, both pinned to the RP2350 platform.

Classes:

- Spi: SPI Master with SpinLock, pin validation, CS management, and retry policy
- SpiSlave: SPI Mode 0 Slave using PIO state machines and double-buffered DMA

Pin constraints for SpiSlave:

    MOSI must equal SCK + 1  (e.g., sck=2, mosi=3)
    CS and MISO can be any GPIO.

"""

from __future__ import annotations
from typing import overload


# ── Spi ──────────────────────────────────────────────────────────────────────

class Spi:
    """
    Industrial-grade SPI Master for RP2350.

    Wraps ``machine.SPI`` with:

    - Hardware SpinLock for multi-core safety
    - CS pin management (active-low by default)
    - Configurable retry policy for transient bus errors
    - Context manager API for atomic multi-transfer sequences
    - Automatic SPI bus ID inference from pin numbers

    Example
    -------
    ```python
        >>> spi = Spi(sck=18, mosi=19, miso=16, cs=17)

        >>> # Single write
        >>> spi.write(b'\\x01\\x02')

        >>> # Atomic multi-transfer with held CS
        >>> with spi.selected() as s:
        ...     s.write(b'\\x9F', hold_cs=True)   # send command
        ...     s.readinto(buf)                    # read response

        >>> spi.deinit()
    ```
    """

    def __init__(
        self,
        *,
        sck: int,
        mosi: int,
        miso: int,
        cs: int,
        cs_active_low: bool = True,
        baudrate: int = 10_000_000,
        polarity: int = 0,
        phase: int = 0,
        bits: int = 8,
        firstbit: int | None = None,
    ) -> None:
        """
        Initialize the SPI Master.

        :param sck: GPIO pin number for SCK
        :param mosi: GPIO pin number for MOSI
        :param miso: GPIO pin number for MISO
        :param cs: GPIO pin number for CS
        :param cs_active_low: CS polarity — True (default) = active LOW
        :param baudrate: Clock frequency in Hz (default: 10 MHz)
        :param polarity: Clock polarity 0 or 1 (default: 0)
        :param phase: Clock phase 0 or 1 (default: 0)
        :param bits: Bits per transfer (default: 8)
        :param firstbit: Bit order — ``machine.SPI.MSB`` (default) or ``LSB``

        :raises ValueError: If any pin is invalid for the inferred SPI bus

        Example
        -------
        ```python
            >>> spi = Spi(sck=18, mosi=19, miso=16, cs=17)
            >>> spi = Spi(sck=10, mosi=11, miso=8, cs=9, baudrate=1_000_000)
        ```
        """
        ...

    @property
    def bus_id(self) -> int:
        """SPI peripheral ID (0 or 1), inferred from pin numbers."""
        ...

    @property
    def pins(self) -> tuple[int, int, int]:
        """``(sck, mosi, miso)`` pin numbers."""
        ...

    @property
    def cs_pin(self) -> int:
        """CS GPIO pin number."""
        ...

    @property
    def last_error(self) -> int:
        """Status code of the last bus operation (``STAT_OK`` = 0 on success)."""
        ...

    def __repr__(self) -> str: ...

    def set_retry_policy(self, *, retries: int | None = None, delay_us: int | None = None) -> None:
        """
        Configure retry behaviour for transient bus errors.

        :param retries: Number of additional attempts after the first failure
        :param delay_us: Delay in microseconds between retries

        Example
        -------
        ```python
            >>> spi.set_retry_policy(retries=3, delay_us=500)
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Release the SPI peripheral.

        Example
        -------
        ```python
            >>> spi.deinit()
        ```
        """
        ...

    def reinit(
        self,
        *,
        baudrate: int | None = None,
        polarity: int | None = None,
        phase: int | None = None,
        bits: int | None = None,
        firstbit: int | None = None,
    ) -> None:
        """
        Re-initialize the SPI peripheral with updated parameters.

        Only the supplied keyword arguments are changed; omitted parameters
        keep their current values.

        :param baudrate: New clock frequency, or ``None`` to keep current
        :param polarity: New clock polarity, or ``None`` to keep current
        :param phase: New clock phase, or ``None`` to keep current
        :param bits: New bits per transfer, or ``None`` to keep current
        :param firstbit: New bit order, or ``None`` to keep current

        Example
        -------
        ```python
            >>> spi.reinit(baudrate=1_000_000)   # slow down only
        ```
        """
        ...

    def select(self) -> None:
        """
        Assert CS and acquire the bus lock manually.

        Must be paired with :meth:`deselect`. Prefer :meth:`selected` for
        automatic cleanup.

        Example
        -------
        ```python
            >>> spi.select()
            >>> spi.write(b'\\x9F', hold_cs=True)
            >>> spi.deselect()
        ```
        """
        ...

    def deselect(self) -> None:
        """
        De-assert CS and release the bus lock manually.

        Must be called after :meth:`select`.
        """
        ...

    def selected(self) -> "Spi":
        """
        Context manager that asserts CS on entry and de-asserts on exit.

        Yields the ``Spi`` instance so callers can chain operations inside
        the ``with`` block with ``hold_cs=True``.

        Example
        -------
        ```python
            >>> with spi.selected() as s:
            ...     s.write(b'\\x9F', hold_cs=True)
            ...     s.readinto(rx_buf)
        ```
        """
        ...

    def write(self, buf: bytes | bytearray) -> None:
        """
        Write *buf* to the SPI bus.

        For multi-transfer sequences with CS held asserted,
        use the :meth:`selected` context manager.

        :param buf: Data to send
        """
        ...

    def readinto(
        self, buf: bytearray, *, write: int = 0xFF
    ) -> None:
        """
        Read into *buf* from the SPI bus, sending *write* as the MOSI byte.

        For multi-transfer sequences with CS held asserted,
        use the :meth:`selected` context manager.

        :param buf: Buffer to read into (length determines byte count)
        :param write: Byte value driven on MOSI during read (default: ``0xFF``)
        """
        ...

    def read(self, n: int, *, write: int = 0xFF) -> bytes:
        """
        Read *n* bytes from the SPI bus.

        For multi-transfer sequences with CS held asserted,
        use the :meth:`selected` context manager.

        :param n: Number of bytes to read
        :param write: Byte value driven on MOSI during read (default: ``0xFF``)
        :return: Received bytes
        """
        ...

    def write_readinto(
        self, wbuf: bytes | bytearray, rbuf: bytearray
    ) -> None:
        """
        Full-duplex transfer: send *wbuf* while reading into *rbuf*.

        For multi-transfer sequences with CS held asserted,
        use the :meth:`selected` context manager.

        :param wbuf: Data to send (must be same length as *rbuf*)
        :param rbuf: Buffer to receive into
        """
        ...

    def write_then_readinto(
        self,
        cmd_bytes: bytes | bytearray,
        rx_buf: bytearray,
        *,
        dummy: int = 0xFF,
    ) -> None:
        """
        Send *cmd_bytes* then read into *rx_buf* in one CS assertion.

        :param cmd_bytes: Command / register address bytes to write first
        :param rx_buf: Buffer to read the response into
        :param dummy: MOSI byte value during the read phase (default: ``0xFF``)
        """
        ...

    def write_then_write(
        self,
        cmd_bytes: bytes | bytearray,
        payload_bytes: bytes | bytearray,
    ) -> None:
        """
        Send *cmd_bytes* followed by *payload_bytes* in one CS assertion.

        :param cmd_bytes: Command / register address bytes
        :param payload_bytes: Payload data bytes
        """
        ...

    def write_u8(self, v: int) -> None:
        """
        Write a single byte to the SPI bus.

        :param v: Byte value (0–255)
        """
        ...

    def read_u8(self) -> int:
        """
        Read a single byte from the SPI bus.

        :return: Received byte value (0–255)
        """
        ...


# ── SpiSlave ──────────────────────────────────────────────────────────────────

class SpiSlave:
    """
    SPI Mode 0 Slave for RP2350 using PIO state machines and DMA.

    Receives data with zero CPU overhead via double-buffered DMA.
    An optional MISO pin enables full-duplex operation.

    Pin constraint:
        ``MOSI`` must be exactly ``SCK + 1``.
        CS and MISO can be any GPIO.

    SM allocation:
        `sm=None` (default) — two consecutive free SMs are found automatically
        via ``find_free_sm()``.
        `sm=<int>` — use that SM for RX; SM+1 automatically used for TX.

    Example
    -------
    ```python
        >>> # RX only
        >>> slave = SpiSlave(sck=2, mosi=3, cs=5)
        >>> data = slave.read()               # block until frame received

        >>> # Full-duplex
        >>> slave = SpiSlave(sck=2, mosi=3, cs=5, miso=4)
        >>> slave.write(bytes([0xAB, 0xCD]))  # pre-load MISO
        >>> rx = slave.read()

        >>> slave.deinit()
    ```
    """

    def __init__(
        self,
        sck: int = 2,
        mosi: int = 3,
        cs: int = 5,
        *,
        sm: int | None = None,
        miso: int | None = None,
        buf_size: int = 8192,
    ) -> None:
        """
        Initialize the SPI Slave.

        :param sck: GPIO pin for SCK (MOSI must equal SCK+1)
        :param mosi: GPIO pin for MOSI (must equal sck+1)
        :param cs: GPIO pin for CS (active LOW)
        :param sm: PIO state machine ID for RX, or ``None`` to auto-allocate
        :param miso: GPIO pin for MISO output, or ``None`` for RX-only mode
        :param buf_size: Size of each DMA receive buffer in bytes (default: 8192)

        :raises ValueError: If ``mosi != sck + 1``

        Example
        -------
        ```python
            >>> slave = SpiSlave(sck=2, mosi=3, cs=5)
            >>> slave = SpiSlave(sck=2, mosi=3, cs=5, miso=4, buf_size=4096)
            >>> slave = SpiSlave(sck=2, mosi=3, cs=5, sm=4)  # explicit SM
        ```
        """
        ...

    def any(self) -> bool:
        """
        Return ``True`` if a complete SPI frame is ready to read.

        Non-blocking. Use before :meth:`read` / :meth:`readinto` to avoid
        blocking.

        Example
        -------
        ```python
            >>> if slave.any():
            ...     data = slave.read(timeout=0)
        ```
        """
        ...

    def read(self, timeout: int = 10000) -> bytes | None:
        """
        Block until a frame arrives and return it as ``bytes``.

        :param timeout: Maximum wait time in milliseconds (default: 10 000)
        :return: Received frame as ``bytes``, or ``None`` on timeout

        Example
        -------
        ```python
            >>> data = slave.read()
            >>> if data is None:
            ...     print("timeout")
        ```
        """
        ...

    def readinto(self, buf: bytearray, timeout: int = 10000) -> int:
        """
        Block until a frame arrives; copy data into *buf*.

        :param buf: Destination buffer
        :param timeout: Maximum wait time in milliseconds (default: 10 000)
        :return: Number of bytes copied, or ``0`` on timeout

        Example
        -------
        ```python
            >>> buf = bytearray(256)
            >>> n = slave.readinto(buf)
            >>> print(buf[:n])
        ```
        """
        ...

    def write(self, data: bytes | bytearray) -> None:
        """
        Pre-load the MISO buffer so the slave sends *data* on the next master
        read cycle.

        Requires ``miso`` pin to be configured. Any in-progress TX DMA is
        safely aborted before reloading.

        :param data: Bytes to send on MISO (truncated to ``buf_size`` if larger)
        :raises OSError: If no MISO pin was configured

        Example
        -------
        ```python
            >>> slave.write(bytes([0x00, 0xFF, 0xA5]))
        ```
        """
        ...

    def writeinto(
        self, data: bytes | bytearray, buf: bytearray, timeout: int = 10000
    ) -> int:
        """
        Full-duplex: pre-load MISO with *data*, then block until an RX frame
        arrives and copy it into *buf*.

        :param data: Bytes to send on MISO
        :param buf: Destination buffer for received data
        :param timeout: Maximum wait time in milliseconds (default: 10 000)
        :return: Number of bytes received, or ``0`` on timeout

        Example
        -------
        ```python
            >>> rx_buf = bytearray(256)
            >>> n = slave.writeinto(bytes([0x00] * 8), rx_buf)
            >>> print(rx_buf[:n])
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Release all PIO state machines and DMA channels.

        Example
        -------
        ```python
            >>> slave.deinit()
        ```
        """
        ...
