"""
XNode System Diagnostics, I2C Scanner & REPL Serial Submodule

Separated from the core xnode/__init__.py to minimize baseline RAM footprint
on the XBee 3 (EFR32MG) MicroPython platform.

Author: PlanXLab Development Team
"""

def get_sys_info() -> tuple[int, int]:
    """Get system core frequency (Hz) and internal temperature (Celsius)."""

def get_mem_info() -> tuple[int, int, int]:
    """Perform garbage collection and return (free, used, total) heap memory in bytes."""

def get_fs_info(path: str = '/') -> tuple[int, int, int, float]:
    """Get filesystem statistics (total, used, free, usage_pct) for the given path."""

def i2cdetect(show: bool = False) -> list[int] | None:
    """Scan I2C bus 1 and return detected device addresses, or print formatted table if show=True."""

class ReplSerial:
    """Serial communication interface over REPL stdin/stdout with timeout support."""
    def __init__(self, timeout: int | float | None = None) -> None: ...
    @property
    def timeout(self) -> int | float | None: ...
    @timeout.setter
    def timeout(self, n: int | float | None) -> None: ...
    def read(self, size: int = 1) -> bytes: ...
    def read_until(self, expected: bytes = b'\n', size: int | None = None) -> bytes: ...
    def readline(self, size: int | None = None) -> bytes: ...
    def write(self, data: bytes | str) -> int: ...
