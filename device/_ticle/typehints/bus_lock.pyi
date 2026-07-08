"""
RP2350 hardware SpinLock primitives and bus status constants.

Provides direct access to the 32 hardware SpinLocks implemented in the
RP2350 Cortex-M33 spinlock registers (base address 0xD0000100).  Each
SpinLock is a 32-bit hardware atomic test-and-set register that enables
zero-overhead mutual exclusion between the two cores without a software
scheduler.

Constants (module-level):

- STAT_OK, STAT_TIMEOUT, STAT_BUS_ERR, STAT_NO_DEVICE: bus operation status flags
- SPI0_SPINLOCK_ID, SPI1_SPINLOCK_ID, I2C0_SPINLOCK_ID, I2C1_SPINLOCK_ID: pre-assigned lock IDs

Classes:

- SpinLock: Thin wrapper around one hardware SpinLock register

"""

# ── Status flag constants ─────────────────────────────────────────────────────

STAT_OK: int
"""Operation completed successfully (value: 0)."""

STAT_TIMEOUT: int
"""Operation timed out (bit 0, value: 1)."""

STAT_BUS_ERR: int
"""Bus error occurred (bit 1, value: 2)."""

STAT_NO_DEVICE: int
"""Target device not found (bit 2, value: 4)."""

# ── Pre-assigned SpinLock IDs ─────────────────────────────────────────────────

SPI0_SPINLOCK_ID: int
"""SpinLock ID reserved for the SPI0 bus (28)."""

SPI1_SPINLOCK_ID: int
"""SpinLock ID reserved for the SPI1 bus (29)."""

I2C0_SPINLOCK_ID: int
"""SpinLock ID reserved for the I2C0 bus (30)."""

I2C1_SPINLOCK_ID: int
"""SpinLock ID reserved for the I2C1 bus (31)."""


class SpinLock:
    """
    Thin wrapper around one RP2350 hardware SpinLock register.

    Hardware SpinLocks are 32-bit MMIO registers.  A read that returns a
    non-zero value atomically claims the lock; writing any value releases it.
    This class exposes ``acquire()`` / ``release()`` and a context-manager
    interface so the lock can be used with ``with`` statements.

    The *polite* mode periodically calls ``machine.idle()`` instead of
    hot-spinning, which reduces power consumption when contention is expected
    to last more than a few hundred CPU cycles.

    :param lock_id: Hardware SpinLock ID, 0–31. IDs 28-31 are pre-assigned to
        SPI0, SPI1, I2C0, I2C1 via the module-level constants.
    :param polite: When ``True``, call ``machine.idle()`` every *yield_every*
        spin iterations instead of busy-waiting.
    :param yield_every: Number of failed attempts before yielding (default: 64).

    :raises ValueError: If ``lock_id`` is not in range 0–31.

    Example
    -------
    ```python
        >>> from ticle_lite.bus_lock import SpinLock, I2C0_SPINLOCK_ID
        >>> lock = SpinLock(lock_id=I2C0_SPINLOCK_ID)
        >>> lock.acquire()
        >>> # ... critical section ...
        >>> lock.release()
        >>>
        >>> # Context manager (preferred)
        >>> with lock:
        ...     # ... critical section ...
        ...     pass
    ```
    """

    def __init__(self, *, lock_id: int, polite: bool = False, yield_every: int = 64) -> None:
        """
        Initialise a SpinLock bound to hardware register *lock_id*.

        :param lock_id: Hardware SpinLock ID, 0–31.
        :param polite: Yield to the idle task when spinning instead of busy-waiting.
        :param yield_every: Spin count between idle yields when *polite* is ``True``.

        :raises ValueError: If ``lock_id`` is not in range 0–31.

        Example
        -------
        ```python
            >>> lock = SpinLock(lock_id=30)
            >>> lock_polite = SpinLock(lock_id=28, polite=True, yield_every=32)
        ```
        """
        ...

    def acquire(self) -> None:
        """
        Spin until the hardware lock is claimed by this core.

        In non-polite mode the loop busy-waits with a tight register poll.
        In polite mode the loop calls ``machine.idle()`` every *yield_every*
        iterations so the other core or low-priority ISRs can make progress.

        Example
        -------
        ```python
            >>> lock = SpinLock(lock_id=30)
            >>> lock.acquire()
            >>> try:
            ...     # ... critical section ...
            ...     pass
            >>> finally:
            ...     lock.release()
        ```
        """
        ...

    def release(self) -> None:
        """
        Release the hardware lock so the other core can acquire it.

        Writing any value to the SpinLock register clears the claim.

        Example
        -------
        ```python
            >>> lock = SpinLock(lock_id=30)
            >>> lock.acquire()
            >>> lock.release()
        ```
        """
        ...

    def __enter__(self) -> "SpinLock":
        """
        Acquire the lock and return ``self`` for use with ``with`` statements.

        :return: This ``SpinLock`` instance.

        Example
        -------
        ```python
            >>> lock = SpinLock(lock_id=I2C0_SPINLOCK_ID)
            >>> with lock:
            ...     i2c.writeto(0x68, b'\\x6B\\x00')
        ```
        """
        ...

    def __exit__(self, et, ev, tb) -> None:
        """
        Release the lock when leaving a ``with`` block.

        :param et: Exception type, or ``None`` if no exception was raised.
        :param ev: Exception value.
        :param tb: Exception traceback.

        Example
        -------
        ```python
            >>> with SpinLock(lock_id=30):
            ...     pass    # lock released automatically on exit
        ```
        """
        ...
