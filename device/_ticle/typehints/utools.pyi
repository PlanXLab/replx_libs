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


def find_free_sm(count: int | None = None) -> list[int]:
    """
    Find available PIO state machine IDs.

    Scans all 12 state machines (PIO0: 0-3, PIO1: 4-7, PIO2: 8-11) and
    returns the IDs of available ones.  SM0 and SM1 are returned last to
    reduce conflicts with I2S, which always claims SM0/SM1 on RP2.

    :param count: Number of SMs to locate. Pass ``None`` to return all
        available SMs.
    :return: List of available SM IDs in preferred allocation order
        (2, 3, 4, … 11, 0, 1).
    :raises ValueError: If *count* is negative.
    :raises RuntimeError: If *count* is specified and fewer than *count*
        state machines are available.

    Example
    -------
    ```python
        >>> from ticle.utils import find_free_sm
        >>> available = find_free_sm()
        >>> print(available)
        [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]
        >>>
        >>> sm_ids = find_free_sm(4)
        >>> print(sm_ids)     # e.g. [2, 3, 4, 5]
        >>>
        >>> # Matrix internally calls find_free_sm(len(pins))
        >>> from ticle_lite.ws2812 import Matrix
        >>> mat = Matrix([0, 1], grid_width=2)   # allocates 2 SMs
    ```
    """
    ...

