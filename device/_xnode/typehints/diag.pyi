"""
XNode System Diagnostics & I2C Scanner Submodule

Separated from the core xnode/__init__.py to minimize baseline RAM footprint
on the XBee 3 (EFR32MG) MicroPython platform.

REPL serial I/O is provided by the XBee-specific `termio_xbee` module,
which replaces the ReplSerial class formerly located in this module.

Author: PlanXLab Development Team
"""

def get_sys_info() -> tuple[int, int]:
    """
    Get system core frequency and internal temperature.

    :return: Tuple of (frequency in Hz, temperature in Celsius).

    Example
    -------
    ```python
        >>> from diag import get_sys_info
        >>> freq, temp = get_sys_info()
        >>> print("CPU:", freq // 1000000, "MHz,", temp, "C")
    ```
    """
    ...

def get_mem_info() -> tuple[int, int, int]:
    """
    Perform garbage collection and return heap memory statistics.

    :return: Tuple of (free, used, total) heap memory in bytes.

    Example
    -------
    ```python
        >>> from diag import get_mem_info
        >>> free, used, total = get_mem_info()
        >>> print("Heap:", used, "/", total, "bytes used")
    ```
    """
    ...

def get_fs_info(path: str = '/') -> tuple[int, int, int, float]:
    """
    Get filesystem statistics for the given path.

    :param path: Mount point or directory to inspect. Defaults to '/'.
    :return: Tuple of (total, used, free, usage_pct) in bytes and percent.

    Example
    -------
    ```python
        >>> from diag import get_fs_info
        >>> total, used, free, pct = get_fs_info('/')
        >>> print("Flash usage:", pct, "%")
    ```
    """
    ...

def i2cdetect(show: bool = False) -> list[int] | None:
    """
    Scan I2C bus 1 for connected devices.

    :param show: If True, print a formatted address table instead of
                 returning the list.
    :return: List of detected 7-bit addresses, or None when show=True.

    Example
    -------
    ```python
        >>> from diag import i2cdetect
        >>> addrs = i2cdetect()
        >>> print([hex(a) for a in addrs])
        >>>
        >>> # Print the familiar i2cdetect-style table
        >>> i2cdetect(show=True)
    ```
    """
    ...
