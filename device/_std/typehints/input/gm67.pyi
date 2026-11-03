"""
UART driver for a GM67 barcode reader.

Example
-------
```python
    >>> from gm67 import GM67
    >>> scanner = GM67()
    >>> scanner.set_trigger_mode(GM67.MODE_CONTINUOUS)
```
"""


class GM67:
    """
    Control a GM67 barcode reader over UART and collect decoded codes.

    :param uart_id: Machine UART peripheral number.
    :param tx_pin: MCU transmit pin connected to the reader's RX.
    :param rx_pin: MCU receive pin connected to the reader's TX.
    :param baudrate: UART baud rate used during initialization.
    :param max_buffer_size: Maximum barcode length in bytes.
    :param char_timeout_ms: Idle interval that terminates an unterminated code.
    :param antipassback_ms: Suppression window for repeated codes; zero disables it.

    Example
    -------
    ```python
        >>> scanner = GM67(uart_id=1, tx_pin=4, rx_pin=5)
        >>> scanner.set_trigger_mode(GM67.MODE_CONTINUOUS)
        >>> scanner.enable_scan()
    ```
    """

    MODE_BUTTON_HOLD: int
    """Scan only while the hardware button is held."""
    MODE_BUTTON_TRIGGER: int
    """Start a scan when the hardware button is pressed."""
    MODE_CONTINUOUS: int
    """Continuously scan while the module is enabled."""
    MODE_HOST: int
    """Scan only when triggered by a host command."""
    MODE_INDUCTION: int
    """Scan when an object is detected by the module."""

    TERM_NONE: int
    """Do not append a terminator to decoded barcode data."""
    TERM_CRLF: int
    """Append carriage return and line feed to decoded data."""
    TERM_CR: int
    """Append carriage return to decoded data."""
    TERM_TAB: int
    """Append a tab character to decoded data."""

    LIGHT_ON_READ: int
    """Illuminate only while decoding a barcode."""
    LIGHT_ALWAYS_ON: int
    """Keep the illumination LED on."""
    LIGHT_ALWAYS_OFF: int
    """Keep the illumination LED off."""

    BAUD_MAP: dict[int, int]
    """Map supported UART baud rates to reader parameter values."""

    uart_id: int
    tx_pin: int
    rx_pin: int
    target_baudrate: int
    char_timeout_ms: int
    antipassback_ms: int
    last_nak_cause: int
    last_profile_error: str | None
    last_response: bytes
    last_baud_sync_responses: dict[int, bytes]
    last_baud_change_response: bytes
    last_baud_change_nak_cause: int

    def __init__(
        self,
        uart_id: int = 1,
        tx_pin: int = 4,
        rx_pin: int = 5,
        baudrate: int = 115200,
        max_buffer_size: int = 512,
        char_timeout_ms: int = 15,
        antipassback_ms: int = 2000,
    ) -> None:
        """
        Initialize the MCU UART and barcode receive buffers.

        :param uart_id: Machine UART peripheral number.
        :param tx_pin: MCU transmit pin connected to the reader's RX.
        :param rx_pin: MCU receive pin connected to the reader's TX.
        :param baudrate: UART baud rate used during initialization.
        :param max_buffer_size: Maximum barcode length in bytes.
        :param char_timeout_ms: Idle interval that terminates an unterminated code.
        :param antipassback_ms: Suppression window for repeated codes; zero disables it.

        :raises ValueError: If buffer size or timeout arguments are invalid.

        Example
        -------
        ```python
            >>> scanner = GM67(uart_id=1, tx_pin=4, rx_pin=5, baudrate=115200)
            >>> scanner.poll()
        ```
        """
        ...

    @staticmethod
    def calc_checksum(payload_without_cs: bytes | bytearray | list[int]) -> tuple[int, int]:
        """
        Calculate the GM67 two-byte additive checksum.

        :param payload_without_cs: Packet bytes that precede the checksum.
        :return: Checksum high byte and low byte.

        Example
        -------
        ```python
            >>> checksum = GM67.calc_checksum(bytes((4, 0xE9, 0x04, 0)))
            >>> len(checksum)
            2
        ```
        """
        ...

    @classmethod
    def build_packet(
        cls,
        opcode: int,
        data: list[int] | None = None,
        permanent: bool = True,
    ) -> bytes:
        """
        Build a checksummed command packet for the scanner.

        :param opcode: Reader command or parameter opcode.
        :param data: Optional command data bytes.
        :param permanent: Save parameter commands in nonvolatile memory.
        :return: Encoded command packet.

        Example
        -------
        ```python
            >>> packet = GM67.build_packet(0xE9, permanent=False)
            >>> len(packet) >= 6
            True
        ```
        """
        ...

    def wakeup(self) -> None:
        """
        Wake the reader by writing the required UART wake-up byte.

        :raises OSError: If the wake-up byte cannot be written.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.wakeup()
        ```
        """
        ...

    def flush(self) -> None:
        """
        Discard pending UART bytes and clear partial or queued barcode data.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.flush()
        ```
        """
        ...

    def send_command(
        self,
        packet: bytes,
        wait_ack: bool = True,
        timeout_ms: int = 250,
    ) -> bool:
        """
        Send a packet and optionally wait for a valid ACK or NAK response.

        :param packet: Complete command packet.
        :param wait_ack: Whether to wait for the reader's response.
        :param timeout_ms: Maximum response wait in milliseconds.
        :return: True for a valid ACK or a successful no-wait write.

        :raises ValueError: If the packet is empty or timeout is negative.
        :raises OSError: If UART write or wake-up fails.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> packet = GM67.build_packet(0xE9, permanent=False)
            >>> acknowledged = scanner.send_command(packet, timeout_ms=500)
        ```
        """
        ...

    def set_parameter(self, param_bytes: list[int], permanent: bool = True) -> bool:
        """
        Write one or more scanner parameters.

        :param param_bytes: Parameter identifier and its value bytes.
        :param permanent: Save the parameter in nonvolatile memory.
        :return: True when the reader acknowledges the update.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> ok = scanner.set_parameter([0x8A, GM67.MODE_HOST], permanent=False)
        ```
        """
        ...

    def start_decode(self) -> bool:
        """
        Start barcode decoding.

        :return: True when the reader acknowledges the command.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.start_decode()
        ```
        """
        ...

    def stop_decode(self) -> bool:
        """
        Stop barcode decoding.

        :return: True when the reader acknowledges the command.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.stop_decode()
        ```
        """
        ...

    def enable_scan(self) -> bool:
        """
        Enable barcode scanning.

        :return: True when the reader acknowledges the command.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.enable_scan()
        ```
        """
        ...

    def disable_scan(self) -> bool:
        """
        Disable barcode scanning.

        :return: True when the reader acknowledges the command.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.disable_scan()
        ```
        """
        ...

    def led_on(self) -> bool:
        """
        Turn on the scanner's indicator LED.

        :return: True when the reader acknowledges the command.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.led_on()
        ```
        """
        ...

    def led_off(self) -> bool:
        """
        Turn off the scanner's indicator LED.

        :return: True when the reader acknowledges the command.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.led_off()
        ```
        """
        ...

    def beep(self, tone: int = 1) -> bool:
        """
        Control the scanner's buzzer.

        :param tone: Nonzero to beep, zero to silence the buzzer.
        :return: True when the reader acknowledges the command.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.beep(tone=1)
        ```
        """
        ...

    def sleep(self) -> bool:
        """
        Put the scanner into its sleep mode.

        :return: True when the reader acknowledges the command.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.sleep()
        ```
        """
        ...

    def reboot_module(self) -> bool:
        """
        Reboot the scanner and clear buffered receive data.

        :return: True when the reset command was written successfully.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.reboot_module()
        ```
        """
        ...

    def set_trigger_mode(self, mode: int) -> bool:
        """
        Select the scanner's trigger mode.

        :param mode: One of the ``MODE_*`` constants.
        :return: True when the reader acknowledges the update.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.set_trigger_mode(GM67.MODE_CONTINUOUS)
        ```
        """
        ...

    def set_terminator(self, term_code: int = TERM_CRLF) -> bool:
        """
        Set the suffix used to terminate scanned barcode text.

        :param term_code: One of ``TERM_NONE``, ``TERM_CRLF``, ``TERM_CR``, or ``TERM_TAB``.
        :return: True when the reader acknowledges the update.

        :raises ValueError: If the terminator code is unsupported.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.set_terminator(GM67.TERM_CRLF)
        ```
        """
        ...

    def set_single_scan_duration(self, tenth_seconds: int = 30) -> bool:
        """
        Set the maximum duration of a single scan attempt.

        :param tenth_seconds: Duration in tenths of a second; the reader clamps it to its supported range.
        :return: True when the reader acknowledges the update.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.set_single_scan_duration(tenth_seconds=30)
        ```
        """
        ...

    def set_same_code_delay(self, hundred_ms: int = 5) -> bool:
        """
        Set the delay before the same barcode may be reported again.

        :param hundred_ms: Delay in units of 100 ms; the reader clamps it to its supported range.
        :return: True when the reader acknowledges the update.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.set_same_code_delay(hundred_ms=10)
        ```
        """
        ...

    def set_lighting(self, mode: int = LIGHT_ON_READ) -> bool:
        """
        Configure the barcode illumination LED.

        :param mode: One of the ``LIGHT_*`` constants.
        :return: True when the reader acknowledges the update.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.set_lighting(GM67.LIGHT_ALWAYS_OFF)
        ```
        """
        ...

    def set_collimation(self, mode: int = LIGHT_ON_READ) -> bool:
        """
        Configure the scanner's aiming light.

        :param mode: One of the ``LIGHT_*`` constants.
        :return: True when the reader acknowledges the update.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.set_collimation(GM67.LIGHT_ON_READ)
        ```
        """
        ...

    def set_decode_beep(self, enable: bool = True) -> bool:
        """
        Enable or disable the beep after a successful decode.

        :param enable: True to beep after each decoded barcode.
        :return: True when the reader acknowledges the update.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.set_decode_beep(False)
        ```
        """
        ...

    def set_silent_mode(self, silent: bool = False) -> bool:
        """
        Enable or disable the scanner's silent mode.

        :param silent: True to suppress scanner sounds.
        :return: True when the reader acknowledges the update.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> scanner.set_silent_mode(True)
        ```
        """
        ...

    def poll(self) -> str | None:
        """
        Return the next complete barcode, if one is available.

        Codes use the configured suffix or ``char_timeout_ms`` idle interval.
        Repeated codes inside ``antipassback_ms`` are suppressed.

        :return: Decoded barcode text, or None when no new code is ready.

        :raises ValueError: If a barcode exceeds ``max_buffer_size``.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> code = scanner.poll()
            >>> if code is not None:
            ...     print("Scanned:", code)
        ```
        """
        ...

    def scan_once(self, timeout_ms: int = 3000) -> str | None:
        """
        Trigger a one-shot scan in temporary host mode.

        :param timeout_ms: Maximum time to wait for a barcode.
        :return: Decoded barcode, or None on timeout or command rejection.

        :raises ValueError: If timeout is negative or a code exceeds the buffer.
        :raises OSError: If decoding cannot be stopped after the scan.

        Example
        -------
        ```python
            >>> scanner = GM67()
            >>> code = scanner.scan_once(timeout_ms=5000)
            >>> if code is not None:
            ...     print(code)
        ```
        """
        ...

    def reset_uart_profile(
        self,
        mode: int = MODE_CONTINUOUS,
        terminator: int = TERM_CRLF,
    ) -> bool:
        """
        Permanently configure and verify the standard 115200-baud UART profile.

        Tries the setup connection at 9600 baud, then at 115200 baud. Failure
        details are recorded in ``last_profile_error``.

        :param mode: Trigger mode to save in the profile.
        :param terminator: Barcode suffix to save in the profile.
        :return: True when every profile setting is applied and verified.

        Example
        -------
        ```python
            >>> scanner = GM67(baudrate=9600)
            >>> configured = scanner.reset_uart_profile(
            ...     mode=GM67.MODE_CONTINUOUS,
            ...     terminator=GM67.TERM_CRLF,
            ... )
            >>> if not configured:
            ...     print(scanner.last_profile_error)
        ```
        """
        ...
