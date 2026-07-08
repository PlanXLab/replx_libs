"""
On-board LED and BOOTSEL button driver for TiCLE Lite (RP2350 / Pico2W).

Provides thin wrappers around the wireless GPIO LED and the ROM-resident
BOOTSEL button so application code can reference familiar names instead of
hardware-specific identifiers.

Classes:

- Led: WL_GPIO0 (wireless subsystem LED), subclass of machine.Pin
- Button: Read-only access to the BOOTSEL button via rp2.bootsel_button()

"""

import machine


class Led(machine.Pin):
    """
    On-board LED (WL_GPIO0) for TiCLE Lite / Pico2W boards.

    Subclasses ``machine.Pin`` and initialises the wireless GPIO0 LED as a
    push-pull output. All ``machine.Pin`` methods (``on()``, ``off()``,
    ``toggle()``, ``value()``) are available.

    Example
    -------
    ```python
        >>> from ticle_lite.basic import Led
        >>> led = Led()
        >>> led.on()
        >>> led.off()
        >>> led.toggle()
    ```
    """

    def __init__(self) -> None:
        """
        Initialise the on-board LED as an output pin.

        Configures WL_GPIO0 as push-pull output with the initial level low.

        Example
        -------
        ```python
            >>> led = Led()
            >>> led.on()
        ```
        """
        ...


class Button:
    """
    Read-only access to the BOOTSEL button via the RP2 ROM.

    Reads the hardware BOOTSEL / user button state without claiming any GPIO
    pin, so the SPI flash bus is unaffected. The value reflects the physical
    button state: ``True`` when pressed, ``False`` when released.

    Example
    -------
    ```python
        >>> from ticle_lite.basic import Button
        >>> if Button.read():
        ...     print("Button pressed")
    ```
    """

    @staticmethod
    def read() -> bool:
        """
        Return the current state of the BOOTSEL button.

        :return: ``True`` if the button is currently pressed, ``False`` otherwise.

        Example
        -------
        ```python
            >>> from ticle_lite.basic import Button
            >>> while not Button.read():
            ...     pass
            >>> print("Button released")
        ```
        """
        ...
