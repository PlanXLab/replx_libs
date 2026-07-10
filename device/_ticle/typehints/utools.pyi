"""
RP2 Utility Functions

Utility functions for RP2040/RP2350 PIO state machine management.
Provides automatic discovery of available PIO resources.

Features:

- Automatic state machine availability scanning
- Conflict-free SM assignment for multi-peripheral applications
- Support for all 12 state machines (PIO0: 0-3, PIO1: 4-7, PIO2: 8-11)

Functions:

- find_free_sm: Find available state machine IDs

"""


def find_free_sm(
    count: int | None = None,
    pio: int | list[int] | tuple[int, ...] | None = None
) -> list[int]:
    """
    Find available PIO state machine IDs.

    Scans PIO SMs and returns those that are currently free.  By default, 
    SM0 and SM1 are returned last to reduce conflicts with physical I2S Audio.
    Can also scan specific PIO blocks (PIO0, PIO1, or PIO2) or collections
    of multiple block numbers.

    :param count: Number of SMs to locate. Pass ``None`` to return all
        available SMs.
    :param pio: PIO block filter. Can be:
        - None: Search all blocks with preferred default order (2, 3, 4, … 11, 0, 1)
        - int (0, 1, or 2): search only in the specified block
        - list/tuple (e.g., [0, 2]): search free SMs within the specified blocks in order of listing.
    :return: List of available SM IDs in preferred allocation order
    :raises ValueError: If *count* is negative, or if *pio* is invalid.
    :raises RuntimeError: If *count* is specified and fewer than *count*
        state machines are available.

    Example
    -------
    ```python
        >>> from ticle.utools import find_free_sm
        >>> available = find_free_sm()
        >>> print(available)
        [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]
        >>>
        >>> sm_ids = find_free_sm(2, pio=2)  # allocate only on PIO2
        >>> print(sm_ids)     # e.g. [8, 9]
        >>>
        >>> # Advanced: allocate across PIO2 then fall back to PIO1
        >>> safe_sms = find_free_sm(2, pio=[2, 1])
    ```
    """
    ...

