"""
I2C Controller Extension for RP2350 (ticle)

Extends I2CController with hardware SpinLock support for multi-core
safe I2C access and includes diagnostic utilities.

Features:

- Hardware SpinLock synchronization for multi-core safety
- Automatic I2C bus ID detection from pin numbers
- Auto-scanning for I2C devices across all valid pin combinations
- Re-exports I2CController and i2cdetect from base module

Classes:

- I2CController: I2CController with SpinLock for RP2350 (extends core I2CController) multi-core

Functions:

- i2cdetect_auto: Auto-detect I2C devices by scanning all pin combinations

"""

from i2c import I2CController as _I2CControllerBase, i2cdetect


class I2CController(_I2CControllerBase):
    """
    I2C Controller with SpinLock support for RP2350.
    
    Extends core I2CController with hardware SpinLock synchronization
    for safe multi-core access. The SpinLock is automatically
    acquired before bus operations and released after.
    
    SpinLocks are allocated from hardware registers at 0xD0000100.
    Each SpinLock provides atomic acquire/release across both cores.

    Example
    -------
    ```python
        >>> # Basic usage (same as core I2CController)
        >>> i2c = I2CController(sda=4, scl=5, id=0)
        >>> devices = i2c.scan()
        >>> 
        >>> # Multi-core safe - SpinLock auto-acquired
        >>> import _thread
        >>> def core1_task():
        ...     val = i2c.read_u8(0x68, 0x75)  # Safe!
        >>> _thread.start_new_thread(core1_task, ())
        >>> 
        >>> # Check SpinLock allocation
        >>> print(f"Lock ID: {i2c._lock_id}")
    ```
    """
    
    def __init__(
        self,
        *,
        sda: int,
        scl: int,
        freq: int = 400_000
    ) -> None:
        """
        Initialize I2C controller.
        
        :param sda: GPIO pin number for SDA
        :param scl: GPIO pin number for SCL
        :param freq: Clock frequency in Hz (default: 400kHz)
        
        :raises ValueError: If pin numbers are invalid
        :raises OSError: If I2C initialization fails

        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
        ```
        """
        ...


def i2cdetect_auto(
    *,
    id: int | None = None,
    sda: int | None = None,
    scl: int | None = None,
    deny_pairs: set[tuple[int, int]] | None = None,
    show: bool = False
) -> list[tuple[tuple[int, int], list[int]]] | None:
    """
    Auto-detect I2C devices by scanning all valid pin combinations.
    
    Scans multiple SDA/SCL pin combinations to find connected I2C devices.
    Useful for discovering wiring when pin assignments are unknown.
    
    :param id: I2C peripheral ID (0 or 1), or None to try both
    :param sda: Specific SDA pin, or None to try all valid pins
    :param scl: Specific SCL pin, or None to try all valid pins
    :param deny_pairs: Set of (sda, scl) tuples to skip
    :param show: Print results to console (default: False)
    :return: List of ((sda, scl), [addresses]) tuples, or None if show=True

    Example
    -------
    ```python
        >>> # Scan all pin combinations
        >>> results = i2cdetect_auto()
        >>> for (sda, scl), addrs in results:
        ...     if addrs:
        ...         print(f"SDA={sda} SCL={scl}: {[hex(a) for a in addrs]}")
        >>> 
        >>> # Scan specific I2C bus
        >>> i2cdetect_auto(id=0, show=True)
        >>> 
        >>> # Skip certain pins (e.g., already in use)
        >>> i2cdetect_auto(deny_pairs={(4, 5), (6, 7)})
    ```
    """
    ...
