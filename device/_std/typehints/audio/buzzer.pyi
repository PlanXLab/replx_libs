"""
PWM-based passive buzzer controller with melody and RTTTL support.

This module provides tone generation and melody playback for passive buzzers
using PWM output. Supports standard note notation and RTTTL (Ring Tone Text
Transfer Language) format for ringtones.

Features:
    - Single note playback with configurable duration
    - Simple beep with frequency and duration
    - Melody playback (blocking and background)
    - RTTTL ringtone format parsing and playback
    - Tempo and volume control
    - Built-in preset melodies

Examples:
    Basic beep and tone:

    >>> from audio.buzzer import Buzzer
    >>> bz = Buzzer(pin=15)
    >>> bz.beep(1000, 200)              # 1kHz for 200ms
    >>> bz.tone('C4', 4)                # Middle C, quarter note
    >>> bz.tone('A#5', 8)               # A# in octave 5, eighth note

    Melody playback:

    >>> melody = ('C4', 4, 'E4', 4, 'G4', 4, 'C5', 2)
    >>> bz.play(melody)                  # Blocking
    >>> bz.play(melody, background=True) # Non-blocking
    >>> bz.stop()                        # Stop playback

    RTTTL ringtone:

    >>> rtttl = "TakeOnMe:d=4,o=4,b=160:8f#5,8f#5,d5,8b,8p,8b,8e5"
    >>> bz.play_rtttl(rtttl)
    >>> # Or parse first for reuse
    >>> melody = Buzzer.parse_rtttl(rtttl)
    >>> bz.play(melody)

    Preset melodies:

    >>> bz.play(Buzzer.MELODY_STARTUP)
    >>> bz.play(Buzzer.MELODY_SUCCESS)
    >>> bz.play(Buzzer.MELODY_ERROR)

Note:
    - Note format: 'C4', 'A#5', 'Gb3' (note + octave)
    - Rest/pause: 'R', 'REST', or 'P'
    - Length: 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth
    - RTTTL is widely used for ringtones and compatible with many sources
"""



class Buzzer:
    """
    PWM-based passive buzzer controller.

    Uses the Pout (PWM) module internally for tone generation.
    Supports musical notation, RTTTL format, and background playback.

    :param pin: GPIO pin number connected to the buzzer
    :param tempo: Playback tempo in BPM (20-300, default 120)
    :param volume: Output volume as percentage (0-100, default 50)

    Example
    -------
    ```python
        >>> bz = Buzzer(15)
        >>> bz.beep()                    # Default 1kHz, 100ms
        >>> bz.tone('A4', 4)             # A4 quarter note (440Hz)
        >>> bz.deinit()
    ```
    """

    MELODY_STARTUP: tuple[str | int, ...]
    """Startup sound: C5-E5-G5 ascending."""

    MELODY_SUCCESS: tuple[str | int, ...]
    """Success sound: G4-C5 two-tone."""

    MELODY_ERROR: tuple[str | int, ...]
    """Error sound: G3-G3 low double beep."""

    MELODY_ALERT: tuple[str | int, ...]
    """Alert sound: A5 triple beep."""

    def __init__(
        self,
        pin: int,
        *,
        tempo: int = 120,
        volume: int = 50
    ) -> None: ...

    def beep(self, freq: int = 1000, ms: int = 100) -> None:
        """
        Play a simple beep at specified frequency.

        Blocking call that plays a tone and returns after completion.

        :param freq: Frequency in Hz (default 1000). Use 0 for silence
        :param ms: Duration in milliseconds (default 100)

        Example
        -------
        ```python
            >>> bz.beep()                # Default 1kHz, 100ms
            >>> bz.beep(440, 500)        # A4 (440Hz) for 500ms
            >>> bz.beep(2000, 50)        # High beep
            >>> bz.beep(0, 200)          # 200ms silence
        ```
        """
        ...

    def tone(self, note: str, length: int = 4, *, staccato: float = 0.9) -> None:
        """
        Play a musical note.

        Blocking call using musical notation for pitch and rhythm.

        :param note: Note name with optional octave (e.g., 'C4', 'A#5', 'Gb3', 'R' for rest)
        :param length: Note duration as fraction of whole note (1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth)
        :param staccato: Sound/silence ratio (0.0-1.0, default 0.9). 1.0 = legato, 0.5 = very short

        Example
        -------
        ```python
            >>> bz.tone('C4')            # Middle C, quarter note
            >>> bz.tone('A4', 2)         # A4 half note
            >>> bz.tone('G5', 8)         # G5 eighth note
            >>> bz.tone('R', 4)          # Quarter rest
            >>> bz.tone('E4', 4, staccato=0.5)  # Short staccato
        ```
        """
        ...

    def silence(self) -> None:
        """
        Stop sound output immediately.

        Equivalent to setting duty cycle to 0 without affecting playback state.

        Example
        -------
        ```python
            >>> bz.tone('C4', 1)         # Start long note
            >>> # ... interrupt ...
            >>> bz.silence()             # Cut sound
        ```
        """
        ...

    def play(self, melody: tuple | list | str) -> bool:
        """
        Play a melody sequence (blocking).

        Accepts either a tuple/list of (note, length) pairs or an RTTTL string.
        RTTTL strings are automatically detected and parsed.

        :param melody: Either tuple/list of (note, length) pairs or RTTTL format string (auto-detected)
        
        :return: True if playback started, False if already playing
        
        :raises ValueError: If RTTTL format is invalid

        Example
        -------
        ```python
            >>> # Tuple format
            >>> melody = ('C4', 4, 'E4', 4, 'G4', 4, 'C5', 2)
            >>> bz.play(melody)
            >>> 
            >>> # RTTTL string (auto-detected)
            >>> bz.play("Nokia:d=4,o=5,b=225:8e6,8d6,f#,g#")
            >>> 
            >>> # Preset melody
            >>> bz.play(Buzzer.MELODY_SUCCESS)
        ```
        """
        ...

    @staticmethod
    def parse_rtttl(rtttl: str) -> tuple:
        """
        Parse RTTTL string into melody tuple.

        RTTTL format: "name:d=duration,o=octave,b=bpm:notes"

        :param rtttl: RTTTL format string
        
        :return: Melody tuple in (note, length, ...) format
        
        :raises ValueError: If format is invalid

        Example
        -------
        ```python
            >>> melody = Buzzer.parse_rtttl(
            ...     "Scale:d=4,o=4,b=120:c,d,e,f,g,a,b,c5"
            ... )
            >>> melody
            ('C4', 4, 'D4', 4, 'E4', 4, 'F4', 4, ...)
        ```
        """
        ...

    def stop(self) -> None:
        """
        Stop current playback and silence output.

        Example
        -------
        ```python
            >>> task = asyncio.create_task(bz.play_async(melody))
            >>> time.sleep(1)
            >>> bz.stop()
        ```
        """
        ...

    @property
    def tempo(self) -> int:
        """
        Current tempo in BPM (beats per minute).
        
        :return: Tempo in BPM

        Example
        -------
        ```python
            >>> bz.tempo
            120
        ```
        """
        ...

    @tempo.setter
    def tempo(self, bpm: int) -> None:
        """
        Set playback tempo.

        :param bpm: Tempo in beats per minute (20-300)
        
        :raises ValueError: If bpm out of range

        Example
        -------
        ```python
            >>> bz.tempo = 140           # Faster
            >>> bz.tempo = 60            # Slower
        ```
        """
        ...

    @property
    def volume(self) -> int:
        """
        Current volume as percentage (0-100).
        
        :return: Volume percentage

        Example
        -------
        ```python
            >>> bz.volume
            50
        ```
        """
        ...

    @volume.setter
    def volume(self, value: int) -> None:
        """
        Set output volume.

        Controls PWM duty cycle. Higher values produce louder sound.

        :param value: Volume percentage (0-100)
        
        :raises ValueError: If value out of range

        Example
        -------
        ```python
            >>> bz.volume = 80           # Louder
            >>> bz.volume = 20           # Quieter
        ```
        """
        ...

    @property
    def is_playing(self) -> bool:
        """
        Check if melody is currently playing.

        :return: True if playback in progress

        Example
        -------
        ```python
            >>> bz.play(melody, background=True)
            >>> bz.is_playing
            True
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Release PWM resources.

        Stops playback and releases the underlying Pout instance.

        Example
        -------
        ```python
            >>> bz = Buzzer(15)
            >>> # ... use buzzer ...
            >>> bz.deinit()
        ```
        """
        ...
