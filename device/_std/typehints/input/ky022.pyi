"""
KY-022 Infrared Receiver Driver

Multi-protocol IR receiver supporting NEC, Samsung, Sony SIRC,
Panasonic, and various HVAC remote control protocols.

Features:

- NEC 8-bit and 16-bit address formats
- Samsung modified NEC protocol
- Sony SIRC 12/15/20-bit formats
- Panasonic (Kaseikyo) 48-bit protocol
- Generic HVAC NEC-series (configurable bit count)
- Carrier 40/84/128-bit protocols
- Repeat code handling with configurable throttling
- Queue-based event delivery

"""

from typing import Tuple


class KY022:
    """
    KY-022 infrared receiver driver.
    
    IRQ-based IR receiver supporting multiple protocols.
    Events are queued and retrieved via get() method.
    
    Example
    -------
    ```python
        >>> from ky022 import KY022
        >>> 
        >>> # Basic NEC remote
        >>> ir = KY022(pin=15)
        >>> 
        >>> while True:
        ...     evt = ir.get(block=True, timeout_ms=5000)
        ...     if evt:
        ...         cmd, addr, ext = evt
        ...         print(f"Command: {cmd}, Address: {addr}")
        >>> 
        >>> # Samsung TV remote
        >>> ir = KY022(pin=15, protocol=KY022.PROTOCOL_SAMSUNG)
        >>> 
        >>> # Sony remote (SIRC 12-bit)
        >>> ir = KY022(pin=15, protocol=KY022.PROTOCOL_SIRC12)
    ```
    """
    
    # Error codes
    REPEAT: int
    BADSTART: int
    BADBLOCK: int
    BADREP: int
    BADDATA: int
    BADADDR: int
    
    # Protocol constants
    PROTOCOL_NEC_8: int
    PROTOCOL_NEC_16: int
    PROTOCOL_SAMSUNG: int
    PROTOCOL_SIRC12: int
    PROTOCOL_SIRC15: int
    PROTOCOL_SIRC20: int
    PROTOCOL_PANA: int
    PROTOCOL_CARRIER40: int
    PROTOCOL_CARRIER84: int
    PROTOCOL_CARRIER128: int
    PROTOCOL_HVAC_NEC: int

    def __init__(
        self,
        pin: int,
        *,
        protocol: int = 1,
        queue_size: int = 16,
        tol_pct: int = 25,
        irq_trigger: int | None = None,
        emit_repeat: bool = True,
        repeat_first_delay_ms: int = 150,
        repeat_min_interval_ms: int = 100,
        hold_throttle_ms: int = 0,
        hvac_bits: int = 0,
        hvac_zero_space_us: int = 560,
        hvac_one_space_us: int = 1690,
        hvac_hdr_mark_us: int = 9000,
        hvac_hdr_space_us: int = 4500
    ) -> None:
        """
        Initialize KY-022 IR receiver.
        
        :param pin: GPIO pin number for IR receiver output
        :param protocol: IR protocol to decode (default: PROTOCOL_NEC_8)
        :param queue_size: Event queue size (default: 16)
        :param tol_pct: Timing tolerance percentage (default: 25)
        :param irq_trigger: IRQ trigger mode (default: Pin.IRQ_FALLING)
        :param emit_repeat: Emit repeat codes to queue (default: True)
        :param repeat_first_delay_ms: Delay before first repeat (default: 150)
        :param repeat_min_interval_ms: Minimum interval between repeats (default: 100)
        :param hold_throttle_ms: Minimum interval between same key reissues, 0=off (default: 0)
        :param hvac_bits: Bit count for PROTOCOL_HVAC_NEC (default: 0)
        :param hvac_zero_space_us: HVAC zero space width in μs (default: 560)
        :param hvac_one_space_us: HVAC one space width in μs (default: 1690)
        :param hvac_hdr_mark_us: HVAC header mark width in μs (default: 9000)
        :param hvac_hdr_space_us: HVAC header space width in μs (default: 4500)
        
        Example
        -------
        ```python
            >>> # Standard NEC remote (LG, most remotes)
            >>> ir = KY022(pin=15, protocol=KY022.PROTOCOL_NEC_8)
            >>> 
            >>> # Extended NEC with 16-bit address
            >>> ir = KY022(pin=15, protocol=KY022.PROTOCOL_NEC_16)
            >>> 
            >>> # Samsung TV remote
            >>> ir = KY022(pin=15, protocol=KY022.PROTOCOL_SAMSUNG)
            >>> 
            >>> # Sony SIRC 12-bit
            >>> ir = KY022(pin=15, protocol=KY022.PROTOCOL_SIRC12)
            >>> 
            >>> # With repeat suppression
            >>> ir = KY022(pin=15, emit_repeat=False)
            >>> 
            >>> # With hold throttling (prevent rapid repeats)
            >>> ir = KY022(pin=15, hold_throttle_ms=200)
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Release hardware resources.
        
        Disables IRQ handler. Safe to call multiple times.
        
        Example
        -------
        ```python
            >>> ir = KY022(pin=15)
            >>> # ... use receiver ...
            >>> ir.deinit()
        ```
        """
        ...

    def get(
        self,
        block: bool = False,
        timeout_ms: int = 1000
    ) -> Tuple[int, int, int] | None:
        """
        Get next IR event from queue.
        
        :param block: Wait for event if queue empty (default: False)
        :param timeout_ms: Maximum wait time in milliseconds (default: 1000)
        :return: Tuple of (command, address, extended) or None if no event
        
        Return value interpretation by protocol:
        
        - NEC/Samsung: (command, address, 0)
        - SIRC: (command, address, extended_device)
        - Panasonic: (command, address, extended_data)
        - HVAC: (byte0, byte1|byte2<<8, byte3|byte4<<8)
        
        Example
        -------
        ```python
            >>> ir = KY022(pin=15)
            >>> 
            >>> # Non-blocking check
            >>> evt = ir.get()
            >>> if evt:
            ...     cmd, addr, ext = evt
            ...     print(f"Received: cmd={cmd}, addr={addr}")
            >>> 
            >>> # Blocking wait with timeout
            >>> evt = ir.get(block=True, timeout_ms=5000)
            >>> if evt is None:
            ...     print("Timeout, no IR signal")
            >>> 
            >>> # Event loop
            >>> while True:
            ...     evt = ir.get(block=True)
            ...     if evt:
            ...         cmd, addr, _ = evt
            ...         if cmd == 0x45:  # Power button
            ...             print("Power pressed!")
        ```
        """
        ...
