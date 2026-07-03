"""
RP2 Utility Functions

Utility functions for RP2040/RP2350 PIO state machine management.
Provides automatic discovery of available PIO resources.

Features:

- Automatic state machine availability scanning
- Conflict-free SM assignment for multi-peripheral applications
- Support for all 12 state machines (PIO0, PIO1, PIO2)

Functions:

- find_free_sm: Find available state machine IDs

"""

def find_free_sm(count: int | None = None) -> list[int]:
    """
    Find available PIO state machine IDs.
    
    Scans all 12 state machines (PIO0: 0-3, PIO1: 4-7, PIO2: 8-11) and
    returns IDs of available ones. This function is useful for classes
    that need state machines to automatically discover available resources.
    
    :param count: Number of SMs needed. If None, returns all available SMs.
    :return: List of available SM IDs in preferred allocation order
    :raises RuntimeError: If count is specified and not enough SMs available
    
    Example
    -------
    Get all available state machines::
    
        >>> from ticle.utils import find_free_sm
        >>> available = find_free_sm()
        >>> # available = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]
    
    Request specific number::
    
        >>> sm_ids = find_free_sm(4)
        >>> # sm_ids = [2, 3, 4, 5]
    
    Used internally by Matrix and other PIO classes::
    
        >>> # Matrix constructor calls find_free_sm(len(pins)) internally
        >>> matrix = Matrix([0, 1, 2, 3], panel_width=16, ...)
    
    Note
    ----
    - RP2040 has 8 state machines (PIO0: 0-3, PIO1: 4-7)
    - RP2350 has 12 state machines (PIO0: 0-3, PIO1: 4-7, PIO2: 8-11)
    - Already-in-use state machines are automatically skipped
    - SM0 and SM1 are returned last to reduce I2S conflicts in automatic PIO allocation
    - When count is specified, scanning stops as soon as enough SMs are found
    - The function temporarily initializes candidate SMs with a NOP program to test availability
    """
    ...
