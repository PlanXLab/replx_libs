"""
PIO-based relay controller for RP2350 with safety features.

Provides multi-channel relay control using PIO state machines with hardware
watchdog, software interlock, and feedback-pin verification for industrial
applications where fail-safe behaviour is required.

Classes:

- Relay: Main relay controller with watchdog, interlock, and feedback support

"""

from typing import overload


class Relay:
    """
    PIO-based multi-channel relay controller with safety features.

    Each relay channel is driven by a dedicated PIO state machine so that
    relay state changes are guaranteed even under heavy Python-level load.
    The optional hardware watchdog turns all relays off if the application
    stops feeding it, ensuring a safe state on software fault.

    :param pins: GPIO pin number for a single relay, or a list/tuple of pin
        numbers for multiple relays.
    :param contact_type: ``Relay.NORMALLY_OPEN`` (default) or
        ``Relay.NORMALLY_CLOSED``.  Controls the electrical meaning of ON/OFF.
    :param interlock_pairs: List of ``(a, b)`` index pairs that are mutually
        exclusive.  Turning either relay on automatically turns the other off.
    :param feedback_pins: Optional GPIO pin numbers to read back the physical
        relay state for verification.
    :param watchdog_ms: Watchdog timeout in milliseconds.  0 disables the
        watchdog.

    :raises ValueError: If no pins are provided.
    :raises RuntimeError: If not enough free state machines are available.

    Example
    -------
    ```python
        >>> from ticle_lite.relay import Relay
        >>> import time
        >>>
        >>> # Motor forward / reverse with interlock
        >>> motor = Relay(
        ...     pins=[16, 17],
        ...     interlock_pairs=[(0, 1)],
        ...     feedback_pins=[18, 19],
        ...     watchdog_ms=5000,
        ... )
        >>> motor.enable_watchdog()
        >>> motor[0].state = Relay.ON    # forward
        >>> assert motor[0].feedback[0]  # verify
        >>>
        >>> while True:
        ...     motor.feed()             # keep watchdog alive
        ...     time.sleep_ms(1000)
    ```
    """

    ON: int
    """Logical ON state (1)."""

    OFF: int
    """Logical OFF state (0)."""

    NORMALLY_OPEN: bool
    """Contact type: relay energised = circuit closed (True)."""

    NORMALLY_CLOSED: bool
    """Contact type: relay energised = circuit open (False)."""

    def __init__(
        self,
        pins: int | list[int] | tuple[int, ...],
        *,
        contact_type: bool = ...,
        interlock_pairs: list[tuple[int, int]] | None = None,
        feedback_pins: list[int] | None = None,
        watchdog_ms: int = 0,
    ) -> None:
        """
        Initialise PIO relay channel(s).

        :param pins: GPIO pin number for a single relay, or list/tuple of pin
            numbers for multiple channels.
        :param contact_type: ``Relay.NORMALLY_OPEN`` or
            ``Relay.NORMALLY_CLOSED`` (default: ``NORMALLY_OPEN``).
        :param interlock_pairs: Mutually-exclusive relay index pairs.
        :param feedback_pins: GPIO pins for reading back relay state.
        :param watchdog_ms: Watchdog timeout in milliseconds (0 = disabled).

        :raises ValueError: If *pins* is empty.
        :raises RuntimeError: If not enough free state machines are available.

        Example
        -------
        ```python
            >>> relay = Relay(pins=16, watchdog_ms=3000)
            >>> relays = Relay(
            ...     pins=[16, 17, 18, 19],
            ...     interlock_pairs=[(0, 1), (2, 3)],
            ...     feedback_pins=[20, 21, 22, 23],
            ...     watchdog_ms=5000,
            ... )
        ```
        """
        ...

    def enable_watchdog(self, timeout_ms: int | None = None) -> "Relay":
        """
        Activate the hardware watchdog.

        Once enabled, ``feed()`` must be called before the timeout expires or
        all relays are de-energised automatically.

        :param timeout_ms: Timeout override in milliseconds.  Uses the value
            passed to ``__init__`` when ``None`` (default).
        :return: ``self`` for method chaining.

        :raises ValueError: If the effective timeout is 0 (watchdog disabled).

        Example
        -------
        ```python
            >>> relay = Relay(pins=16, watchdog_ms=5000)
            >>> relay.enable_watchdog()   # use constructor timeout
            >>> relay.enable_watchdog(timeout_ms=2000)  # override
        ```
        """
        ...

    def feed(self) -> None:
        """
        Reset the watchdog timer to prevent an automatic relay shutdown.

        Must be called periodically whenever the watchdog is enabled.  A
        common pattern is to call ``feed()`` once per main-loop iteration.

        Example
        -------
        ```python
            >>> relay = Relay(pins=16, watchdog_ms=3000)
            >>> relay.enable_watchdog()
            >>> relay[0].state = Relay.ON
            >>> while True:
            ...     relay.feed()
            ...     time.sleep_ms(500)
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Turn off all relays and release PIO resources.

        Safe to call multiple times.

        Example
        -------
        ```python
            >>> relay = Relay(pins=[16, 17])
            >>> relay.deinit()
        ```
        """
        ...

    def __enter__(self) -> "Relay":
        """
        Return ``self`` for use as a context manager.

        :return: This ``Relay`` instance.

        Example
        -------
        ```python
            >>> with Relay(pins=16) as relay:
            ...     relay[0].state = Relay.ON
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Call ``deinit()`` when leaving the ``with`` block.

        :param exc_type: Exception type, or ``None``.
        :param exc_val: Exception value.
        :param exc_tb: Traceback.

        Example
        -------
        ```python
            >>> with Relay(pins=16) as relay:
            ...     relay[0].state = Relay.ON
            ... # deinit() called automatically here
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return the number of relay channels.

        :return: Channel count.

        Example
        -------
        ```python
            >>> relay = Relay(pins=[16, 17, 18])
            >>> len(relay)
            3
        ```
        """
        ...

    @overload
    def __getitem__(self, idx: int) -> "_View": ...
    @overload
    def __getitem__(self, idx: slice) -> "_View": ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Return a view for one or more relay channels.

        :param idx: Integer index or slice.
        :return: Reusable ``_View`` for the selected channel(s).

        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> relay = Relay(pins=[16, 17, 18, 19])
            >>> relay[0].state = Relay.ON     # single channel
            >>> relay[1:3].state = Relay.OFF  # channels 1 and 2
            >>> relay[:].all_off()            # all channels
        ```
        """
        ...

    def verify_feedback(self, idx: int) -> bool | None:
        """
        Verify that relay *idx* matches the expected logical state.

        :param idx: Relay channel index.
        :return: ``True`` if feedback matches logical state, ``False`` if
            mismatch, ``None`` if no feedback pin was configured.

        Example
        -------
        ```python
            >>> relay = Relay(pins=16, feedback_pins=[17])
            >>> relay[0].state = Relay.ON
            >>> ok = relay.verify_feedback(0)
            >>> if ok is False:
            ...     print("Relay failed to switch!")
        ```
        """
        ...

    def verify_all_feedback(self) -> list[bool | None]:
        """
        Verify all relay channels against their configured feedback pins.

        :return: List of ``True`` / ``False`` / ``None`` values, one per
            channel (``None`` when no feedback pin is configured).

        Example
        -------
        ```python
            >>> relay = Relay(pins=[16, 17], feedback_pins=[18, 19])
            >>> relay[:].state = Relay.ON
            >>> results = relay.verify_all_feedback()
            >>> if not all(r is not False for r in results):
            ...     relay.emergency_stop()
        ```
        """
        ...

    def all_off(self) -> None:
        """
        De-energise all relay channels.

        Example
        -------
        ```python
            >>> relay = Relay(pins=[16, 17, 18])
            >>> relay[:].state = Relay.ON
            >>> relay.all_off()
        ```
        """
        ...

    def emergency_stop(self) -> None:
        """
        Immediately de-energise all relays via direct PIO register writes.

        Bypasses logical state tracking for the fastest possible shutdown.
        After an emergency stop, reinitialise the object before reuse.

        Example
        -------
        ```python
            >>> relay = Relay(pins=[16, 17])
            >>> if sensor.fault_detected():
            ...     relay.emergency_stop()
        ```
        """
        ...

    class _View:
        """
        Reusable view for one or more relay channels.

        Returned by ``Relay.__getitem__()``.  Not instantiated directly.

        Example
        -------
        ```python
            >>> relay = Relay(pins=[16, 17, 18, 19])
            >>> relay[0].state = Relay.ON
            >>> relay[0:2].toggle()
            >>> relay[:].all_off()
        ```
        """

        def __getitem__(self, idx: int | slice) -> "Relay._View":
            """
            Return a narrower view from this view.

            :param idx: View-local index or slice.
            :return: Reusable ``_View`` for the selected channel(s).

            Example
            -------
            ```python
                >>> relay = Relay(pins=[16, 17, 18, 19])
                >>> view = relay[:]
                >>> view[0].state = Relay.ON
            ```
            """
            ...

        def __len__(self) -> int:
            """
            Return the number of channels in this view.

            :return: Channel count.

            Example
            -------
            ```python
                >>> relay = Relay(pins=[16, 17, 18])
                >>> len(relay[:])
                3
            ```
            """
            ...

        @property
        def state(self) -> list[int]:
            """
            Read the logical state of selected channels.

            :return: List of states — each element is ``Relay.ON`` (1) or
                ``Relay.OFF`` (0).

            Example
            -------
            ```python
                >>> relay = Relay(pins=[16, 17])
                >>> relay[0].state = Relay.ON
                >>> print(relay[:].state)
                [1, 0]
            ```
            """
            ...

        @state.setter
        def state(self, value: int | list[int]) -> None:
            """
            Set the logical state of selected channels.

            :param value: Single integer applied to all selected channels, or
                a list with one value per channel.

            Example
            -------
            ```python
                >>> relay = Relay(pins=[16, 17])
                >>> relay[0].state = Relay.ON
                >>> relay[:].state = [Relay.ON, Relay.OFF]
            ```
            """
            ...

        @property
        def contact_type(self) -> list[bool]:
            """
            Read the contact type of selected channels.

            :return: List of contact types — ``Relay.NORMALLY_OPEN`` or
                ``Relay.NORMALLY_CLOSED`` for each channel.

            Example
            -------
            ```python
                >>> relay = Relay(pins=[16, 17])
                >>> print(relay[:].contact_type)
                [True, True]
            ```
            """
            ...

        @contact_type.setter
        def contact_type(self, ct: bool) -> None:
            """
            Set the contact type for all selected channels.

            :param ct: ``Relay.NORMALLY_OPEN`` or ``Relay.NORMALLY_CLOSED``.

            Example
            -------
            ```python
                >>> relay = Relay(pins=[16, 17])
                >>> relay[:].contact_type = Relay.NORMALLY_CLOSED
            ```
            """
            ...

        @property
        def feedback(self) -> list[bool | None]:
            """
            Verify selected channels against their feedback pins.

            :return: List of ``True`` (match), ``False`` (mismatch), or
                ``None`` (no feedback pin) for each channel.

            Example
            -------
            ```python
                >>> relay = Relay(pins=16, feedback_pins=[17])
                >>> relay[0].state = Relay.ON
                >>> if relay[0].feedback[0] is False:
                ...     raise RuntimeError("Relay stuck")
            ```
            """
            ...

        def toggle(self) -> None:
            """
            Invert the state of selected channels.

            Example
            -------
            ```python
                >>> relay = Relay(pins=[16, 17])
                >>> relay[0].state = Relay.ON
                >>> relay[0].toggle()   # now OFF
                >>> relay[0].toggle()   # now ON again
            ```
            """
            ...

        def pulse(self, duration_ms: int, state: int = 1) -> None:
            """
            Apply *state* for *duration_ms* milliseconds, then revert.

            :param duration_ms: Pulse duration in milliseconds.
            :param state: State during the pulse (default: ``Relay.ON``).

            Example
            -------
            ```python
                >>> relay = Relay(pins=16)
                >>> relay[0].pulse(500)          # 500 ms ON pulse
                >>> relay[0].pulse(200, Relay.OFF)  # 200 ms OFF pulse
            ```
            """
            ...

        def all_off(self) -> None:
            """
            De-energise all channels in this view.

            Example
            -------
            ```python
                >>> relay = Relay(pins=[16, 17, 18])
                >>> relay[:].state = Relay.ON
                >>> relay[:].all_off()
            ```
            """
            ...

        def emergency_stop(self) -> None:
            """
            Immediately de-energise selected relays via direct PIO register
            writes.

            Example
            -------
            ```python
                >>> relay = Relay(pins=[16, 17])
                >>> relay[:].emergency_stop()
            ```
            """
            ...
