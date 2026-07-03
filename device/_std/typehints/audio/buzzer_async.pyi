"""
Async wrapper for PWM-based passive buzzer controller.

Provides asyncio-compatible interface for non-blocking tone and melody
playback in cooperative multitasking environments.

Example
-------
```python
    >>> import asyncio
    >>> from buzzer import Buzzer
    >>> from buzzer_async import BuzzerAsync
    >>> 
    >>> async def main():
    ...     bz = Buzzer(pin=15)
    ...     async_bz = BuzzerAsync(bz)
    ...     
    ...     # Async beep
    ...     await async_bz.beep(1000, 200)
    ...     
    ...     # Async melody (non-blocking)
    ...     await async_bz.play(Buzzer.MELODY_STARTUP)
    >>> 
    >>> asyncio.run(main())
```

"""

from .buzzer import Buzzer


class BuzzerAsync:
    """
    Async wrapper for Buzzer.
    
    Wraps a Buzzer instance to provide asyncio-compatible methods.
    Yields control during delays to allow other coroutines to run.
    
    Example
    -------
    ```python
        >>> # With MQTT client
        >>> async def alert_task(async_bz, mqtt):
        ...     async for msg in mqtt.messages():
        ...         if msg.topic == "alert":
        ...             await async_bz.play(Buzzer.MELODY_ALERT)
    ```
    """

    def __init__(self, buzzer: "Buzzer") -> None:
        """
        Initialize async wrapper.
        
        :param buzzer: Buzzer instance to wrap.
        """
        ...

    @property
    def buzzer(self) -> "Buzzer":
        """
        Get underlying Buzzer instance.
        
        :return: The wrapped Buzzer.
        
        Example
        -------
        ```python
            >>> async_bz.buzzer
            <Buzzer object at ...>
        ```
        """
        ...

    @property
    def tempo(self) -> int:
        """
        Get playback tempo in BPM.
        
        :return: Current tempo (20-300).
        
        Example
        -------
        ```python
            >>> async_bz.tempo
            120
        ```
        """
        ...

    @tempo.setter
    def tempo(self, bpm: int) -> None:
        """
        Set playback tempo.
        
        :param bpm: Tempo in BPM (20-300).
        :raises ValueError: If bpm out of range.
        
        Example
        -------
        ```python
            >>> async_bz.tempo = 140
        ```
        """
        ...

    @property
    def volume(self) -> int:
        """
        Get output volume.
        
        :return: Current volume (0-100).
        
        Example
        -------
        ```python
            >>> async_bz.volume
            50
        ```
        """
        ...

    @volume.setter
    def volume(self, value: int) -> None:
        """
        Set output volume.
        
        :param value: Volume percentage (0-100).
        :raises ValueError: If value out of range.
        
        Example
        -------
        ```python
            >>> async_bz.volume = 80
        ```
        """
        ...

    @property
    def is_playing(self) -> bool:
        """
        Check if melody is currently playing.
        
        :return: True if playing, False otherwise.
        
        Example
        -------
        ```python
            >>> async_bz.is_playing
            False
        ```
        """
        ...

    async def beep(self, freq: int = 1000, ms: int = 100) -> None:
        """
        Play a simple beep at specified frequency (async).

        :param freq: Frequency in Hz (default 1000). Use 0 for silence.
        :param ms: Duration in milliseconds (default 100).

        Example
        -------
        ```python
            >>> await async_bz.beep()           # Default 1kHz, 100ms
            >>> await async_bz.beep(440, 500)   # A4 (440Hz) for 500ms
        ```
        """
        ...

    async def tone(self, note: str, length: int = 4, *, staccato: float = 0.9) -> None:
        """
        Play a musical note (async).

        :param note: Note name with optional octave (e.g., 'C4', 'A#5').
        :param length: Note duration (1=whole, 2=half, 4=quarter, etc.).
        :param staccato: Sound/silence ratio (0.0-1.0, default 0.9).

        Example
        -------
        ```python
            >>> await async_bz.tone('C4')       # Middle C, quarter note
            >>> await async_bz.tone('A4', 2)    # A4 half note
        ```
        """
        ...

    async def play(self, melody: tuple | list | str, *, staccato: float = 0.9) -> None:
        """
        Play a melody sequence (async).

        Yields control between notes, allowing other coroutines to run.

        :param melody: Tuple/list of (note, length) pairs or RTTTL string.
        :param staccato: Sound/silence ratio for all notes (default 0.9).

        Example
        -------
        ```python
            >>> # Tuple format
            >>> melody = ('C4', 4, 'E4', 4, 'G4', 4, 'C5', 2)
            >>> await async_bz.play(melody)
            >>> 
            >>> # RTTTL string
            >>> await async_bz.play("Nokia:d=4,o=5,b=225:8e6,8d6,f#,g#")
            >>> 
            >>> # Preset melody
            >>> await async_bz.play(Buzzer.MELODY_SUCCESS)
        ```
        """
        ...

    def stop(self) -> None:
        """
        Stop melody playback.
        
        Sets is_playing to False and silences output.
        
        Example
        -------
        ```python
            >>> async_bz.stop()
        ```
        """
        ...

    def silence(self) -> None:
        """
        Stop sound output immediately.
        
        Example
        -------
        ```python
            >>> async_bz.silence()
        ```
        """
        ...
