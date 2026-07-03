"""
PWM Output Driver.

Provides allocation-conscious PWM output for one or more channels. Scalar
methods default to channel 0, while indexed views support multi-channel access
with reused result lists.

Example
-------
```python
    >>> from pout import Pout
    >>> pwm = Pout([16, 17], freq=1000)
    >>> pwm.set_duty(50)
    >>> pwm.set_duty(25, idx=1)
    >>> pwm[:].duty = [10, 90]
    >>> pwm.deinit()
```
"""

class Pout:
    """
    Multi-channel PWM output.

    :param pins: Single GPIO pin number or list/tuple of pin numbers.
    :param freq: Initial PWM frequency in Hz.
    :param duty_u16: Initial raw duty value, 0..65535.

    Example
    -------
    ```python
        >>> pwm = Pout(16, freq=1000)
        >>> pwm.set_duty(50)
    ```
    """

    def __init__(self, pins: int | list[int] | tuple[int, ...], *, freq: int = 1000, duty_u16: int = 0) -> None:
        """
        Initialize PWM channel(s).

        :param pins: GPIO pin number or pin sequence.
        :param freq: PWM frequency in Hz.
        :param duty_u16: Initial duty value.

        Example
        -------
        ```python
            >>> pwm = Pout([16, 17], freq=500, duty_u16=0)
        ```
        """
        ...

    def __enter__(self) -> "Pout":
        """
        Enter context manager.

        :return: This Pout instance.

        Example
        -------
        ```python
            >>> with Pout(16) as pwm:
            ...     pwm.set_duty(50)
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context manager and deinitialize PWM.

        Example
        -------
        ```python
            >>> with Pout(16) as pwm:
            ...     pass
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return number of PWM channels.

        :return: Channel count.

        Example
        -------
        ```python
            >>> len(Pout([16, 17]))
            2
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "Pout._View":
        """
        Get view for PWM channel(s).

        :param idx: Channel index or slice.
        :return: Reusable view for selected channel(s).
        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> pwm = Pout([16, 17])
            >>> pwm[0].duty = 50
            >>> pwm[:].freq = 1000
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Turn off and release PWM channels.

        Example
        -------
        ```python
            >>> pwm = Pout(16)
            >>> pwm.deinit()
        ```
        """
        ...

    def freq(self, idx: int = 0) -> int:
        """
        Return channel frequency in Hz.

        :param idx: Channel index.
        :return: Frequency in Hz.

        Example
        -------
        ```python
            >>> pwm.freq()
        ```
        """
        ...

    def set_freq(self, hz: int = 1000, idx: int = 0) -> None:
        """
        Set channel frequency.

        :param hz: Frequency in Hz.
        :param idx: Channel index.
        :raises ValueError: If hz is not positive.

        Example
        -------
        ```python
            >>> pwm.set_freq(2000, idx=1)
        ```
        """
        ...

    def set_freq_all(self, hz: int) -> None:
        """
        Set frequency for all channels.

        :param hz: Frequency in Hz.

        Example
        -------
        ```python
            >>> pwm.set_freq_all(1000)
        ```
        """
        ...

    def period_us(self, idx: int = 0) -> int:
        """
        Return PWM period in microseconds.

        :param idx: Channel index.
        :return: Period in microseconds.

        Example
        -------
        ```python
            >>> pwm.period_us()
        ```
        """
        ...

    def set_period_us(self, us: int = 1000, idx: int = 0) -> None:
        """
        Set PWM period in microseconds.

        :param us: Period in microseconds.
        :param idx: Channel index.

        Example
        -------
        ```python
            >>> pwm.set_period_us(20000)
        ```
        """
        ...

    def duty(self, idx: int = 0) -> float:
        """
        Return duty percentage.

        :param idx: Channel index.
        :return: Duty percentage, 0.0..100.0.

        Example
        -------
        ```python
            >>> pwm.duty()
        ```
        """
        ...

    def set_duty(self, percent: float = 0, idx: int = 0) -> None:
        """
        Set duty percentage.

        :param percent: Duty percentage, clamped to 0..100.
        :param idx: Channel index.

        Example
        -------
        ```python
            >>> pwm.set_duty(75, idx=1)
        ```
        """
        ...

    def duty_u16(self, idx: int = 0) -> int:
        """
        Return raw duty value.

        :param idx: Channel index.
        :return: Duty value, 0..65535.

        Example
        -------
        ```python
            >>> pwm.duty_u16()
        ```
        """
        ...

    def set_duty_u16(self, value: int = 0, idx: int = 0) -> None:
        """
        Set raw duty value.

        :param value: Duty value, clamped to 0..65535.
        :param idx: Channel index.

        Example
        -------
        ```python
            >>> pwm.set_duty_u16(32768)
        ```
        """
        ...

    def duty_us(self, idx: int = 0) -> int:
        """
        Return high pulse width in microseconds.

        :param idx: Channel index.
        :return: Pulse width in microseconds.

        Example
        -------
        ```python
            >>> pwm.duty_us()
        ```
        """
        ...

    def set_duty_us(self, us: int = 0, idx: int = 0) -> None:
        """
        Set high pulse width in microseconds.

        :param us: Pulse width in microseconds.
        :param idx: Channel index.

        Example
        -------
        ```python
            >>> pwm.set_duty_us(1500)
        ```
        """
        ...

    def enabled(self, idx: int = 0) -> bool:
        """
        Return logical enable state.

        :param idx: Channel index.
        :return: True if output is enabled.

        Example
        -------
        ```python
            >>> pwm.enabled()
        ```
        """
        ...

    def enable(self, flag: bool = True, idx: int = 0) -> None:
        """
        Enable or disable output without losing duty setting.

        :param flag: True to enable, False to force output low.
        :param idx: Channel index.

        Example
        -------
        ```python
            >>> pwm.enable(False)
        ```
        """
        ...

    class _View:
        """
        Reusable view for selected PWM channels.

        Property getters return an internal reused list. Copy it when retaining
        a snapshot.

        Example
        -------
        ```python
            >>> pwm = Pout([16, 17])
            >>> pwm[:].duty = [25, 75]
        ```
        """
        __slots__ = ("_p", "_i", "_cache")
        def __len__(self) -> int:
            """
            Return number of channels in the view.

            :return: View channel count.

            Example
            -------
            ```python
                >>> len(pwm[:])
            ```
            """
            ...

        def __getitem__(self, idx: int | slice) -> "Pout._View":
            """
            Narrow the current view.

            :param idx: View-relative index or slice.
            :return: Reusable narrowed view.

            Example
            -------
            ```python
                >>> pwm[:][0].duty = 50
            ```
            """
            ...

        def period_us(self) -> int:
            """
            Return period for a single-channel view.

            :return: Period in microseconds.
            :raises ValueError: If the view has more than one channel.

            Example
            -------
            ```python
                >>> pwm[0].period_us()
            ```
            """
            ...

        def set_freq(self, hz: int) -> None:
            """
            Set frequency for all view channels.

            :param hz: Frequency in Hz.

            Example
            -------
            ```python
                >>> pwm[:].set_freq(1000)
            ```
            """
            ...

        def set_period_us(self, us: int) -> None:
            """
            Set period for all view channels.

            :param us: Period in microseconds.

            Example
            -------
            ```python
                >>> pwm[:].set_period_us(20000)
            ```
            """
            ...

        def set_duty(self, percent: float) -> None:
            """
            Set duty percentage for all view channels.

            :param percent: Duty percentage.

            Example
            -------
            ```python
                >>> pwm[:].set_duty(50)
            ```
            """
            ...

        def set_duty_u16(self, value: int) -> None:
            """
            Set raw duty for all view channels.

            :param value: Duty value, 0..65535.

            Example
            -------
            ```python
                >>> pwm[:].set_duty_u16(32768)
            ```
            """
            ...

        def set_duty_us(self, us: int) -> None:
            """
            Set pulse width for all view channels.

            :param us: Pulse width in microseconds.

            Example
            -------
            ```python
                >>> pwm[:].set_duty_us(1500)
            ```
            """
            ...

        def enable(self, flag: bool = True) -> None:
            """
            Enable or disable all view channels.

            :param flag: Enable state.

            Example
            -------
            ```python
                >>> pwm[:].enable(False)
            ```
            """
            ...

        @property
        def freq(self) -> list[int]:
            """
            Get view frequencies.

            :return: Reused list of frequencies.

            Example
            -------
            ```python
                >>> freqs = pwm[:].freq.copy()
            ```
            """
            ...

        @freq.setter
        def freq(self, hz: int | list[int] | tuple[int, ...]) -> None:
            """
            Set view frequencies.

            :param hz: Scalar frequency or sequence matching the view length.

            Example
            -------
            ```python
                >>> pwm[:].freq = [500, 1000]
            ```
            """
            ...

        @property
        def period(self) -> list[int]:
            """
            Get view periods.

            :return: Reused list of periods in microseconds.

            Example
            -------
            ```python
                >>> periods = pwm[:].period.copy()
            ```
            """
            ...

        @period.setter
        def period(self, us: int | list[int] | tuple[int, ...]) -> None:
            """
            Set view periods.

            :param us: Scalar period or sequence matching the view length.

            Example
            -------
            ```python
                >>> pwm[:].period = 20000
            ```
            """
            ...

        @property
        def duty(self) -> list[float]:
            """
            Get view duty percentages.

            :return: Reused list of duty percentages.

            Example
            -------
            ```python
                >>> duty = pwm[:].duty.copy()
            ```
            """
            ...

        @duty.setter
        def duty(self, percent: float | list[float] | tuple[float, ...]) -> None:
            """
            Set view duty percentages.

            :param percent: Scalar duty or sequence matching the view length.

            Example
            -------
            ```python
                >>> pwm[:].duty = [10, 90]
            ```
            """
            ...

        @property
        def duty_u16(self) -> list[int]:
            """
            Get raw duty values.

            :return: Reused list of raw duty values.

            Example
            -------
            ```python
                >>> raw = pwm[:].duty_u16.copy()
            ```
            """
            ...

        @duty_u16.setter
        def duty_u16(self, value: int | list[int] | tuple[int, ...]) -> None:
            """
            Set raw duty values.

            :param value: Scalar raw duty or sequence matching the view length.

            Example
            -------
            ```python
                >>> pwm[:].duty_u16 = [0, 65535]
            ```
            """
            ...

        @property
        def duty_us(self) -> list[int]:
            """
            Get high pulse widths.

            :return: Reused list of pulse widths in microseconds.

            Example
            -------
            ```python
                >>> pulses = pwm[:].duty_us.copy()
            ```
            """
            ...

        @duty_us.setter
        def duty_us(self, us: int | list[int] | tuple[int, ...]) -> None:
            """
            Set high pulse widths.

            :param us: Scalar pulse width or sequence matching the view length.

            Example
            -------
            ```python
                >>> pwm[:].duty_us = [1000, 2000]
            ```
            """
            ...

        @property
        def enabled(self) -> list[bool]:
            """
            Get enable states.

            :return: Reused list of enable states.

            Example
            -------
            ```python
                >>> enabled = pwm[:].enabled.copy()
            ```
            """
            ...

        @enabled.setter
        def enabled(self, flag: bool | list[bool] | tuple[bool, ...]) -> None:
            """
            Set enable states.

            :param flag: Scalar state or sequence matching the view length.

            Example
            -------
            ```python
                >>> pwm[:].enabled = [True, False]
            ```
            """
            ...
