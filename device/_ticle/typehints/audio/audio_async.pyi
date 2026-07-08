"""
Asyncio-compatible I2S audio adapter for the Audio class.

Wraps a synchronous Audio instance and provides non-blocking coroutines for
all blocking audio operations. Each TX coroutine writes data to the I2S DMA
buffer in ibuf-sized batches, yielding to the event loop once per full
DMA buffer. This prevents DMA underrun that causes audio tearing while
still allowing other tasks to run during long playback.

Features:
    - Non-blocking tone, note-sequence, PCM16, and WAV playback
    - Non-blocking in-memory capture and WAV file recording
    - is_playing / is_recording properties for state monitoring
    - Task cancellation supported via asyncio task.cancel()
    - Adapter pattern: wraps an existing Audio instance

Examples:
    Concurrent WAV playback and button handling:

    >>> import asyncio
    >>> from ticle_lite.audio import Audio
    >>> from ticle_lite.audio_async import AsyncAudio
    >>> from ticle_lite.button import Button
    >>>
    >>> audio = Audio(sck=4, ws=5, sd_out=7, sd_in=6)
    >>> aa = AsyncAudio(audio)
    >>> btn = Button([16, 17, 18, 19])
    >>>
    >>> async def play_task():
    ...     await aa.play('/res/fanfare2.wav')
    >>>
    >>> async def ui_task():
    ...     while aa.is_playing:
    ...         for i, ev in btn.update():
    ...             if ev == 'click':
    ...                 print('button', i)
    ...         await asyncio.sleep_ms(10)
    >>>
    >>> async def main():
    ...     await asyncio.gather(play_task(), ui_task())
    >>>
    >>> asyncio.run(main())

    Melody playback with concurrent display update:

    >>> TETRIS = ('E5', 4, 'B4', 8, 'C5', 8, ...)
    >>>
    >>> async def main():
    ...     await asyncio.gather(
    ...         aa.note(TETRIS),
    ...         display_task(),
    ...     )

    Stop playback early:

    >>> async def main():
    ...     task = asyncio.create_task(aa.play('/res/jingle_bells_x.wav'))
    ...     await asyncio.sleep_ms(2000)
    ...     task.cancel()
    ...     await asyncio.sleep_ms(0)

    Non-blocking recording:

    >>> async def main():
    ...     await asyncio.gather(
    ...         aa.record_to_file('/rec.wav', 5000),
    ...         led_blink_task(),
    ...     )

Note:
    - Playback and recording cannot run simultaneously (shared I2S bus).
    - Only WAV files with 8/16-bit PCM, mono or stereo are supported.
    - On RP2, machine.I2S implements the asyncio stream protocol.
    - RP2350: I2S is deinited before each flash write in record_to_file().
"""

from audio.audio import Audio


class AsyncAudio:
    """
    Asyncio adapter for I2S audio operations.

    Wraps a synchronous Audio instance and provides async coroutines for
    all blocking TX and RX operations. Playback coroutines use
    asyncio.StreamWriter to yield to the event loop at each DMA chunk;
    recording coroutines yield while waiting for RX data.

    :param audio: An initialized Audio instance to wrap.

    Example
    -------
    ```python
        >>> import asyncio
        >>> from ticle_lite.audio import Audio
        >>> from ticle_lite.audio_async import AsyncAudio
        >>>
        >>> audio = Audio(sck=4, ws=5, sd_out=7, sd_in=6)
        >>> aa = AsyncAudio(audio)
        >>>
        >>> async def main():
        ...     await asyncio.gather(aa.play('/res/come_get_it.wav'), other_task())
        >>>
        >>> asyncio.run(main())
    ```
    """

    def __init__(self, audio: Audio) -> None:
        """
        Create an async adapter for an Audio instance.

        :param audio: The Audio instance to wrap.
        """
        ...

    def __enter__(self) -> "AsyncAudio":
        """
        Return ``self`` for use as a context manager.

        :return: This ``AsyncAudio`` instance.

        Example
        -------
        ```python
            >>> audio = Audio(sck=4, ws=5, sd_out=7, sd_in=6)
            >>> async def main():
            ...     with AsyncAudio(audio) as aa:
            ...         await aa.tone(440, 300)
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Call deinit() on the underlying Audio when used as context manager."""
        ...

    @property
    def audio(self) -> Audio:
        """The underlying synchronous Audio instance."""
        ...

    @property
    def is_playing(self) -> bool:
        """
        True while a tone(), note(), play_pcm16(), or play() coroutine is active.

        Example
        -------
        ```python
            >>> async def ui():
            ...     while aa.is_playing:
            ...         await asyncio.sleep_ms(50)
        ```
        """
        ...

    @property
    def is_recording(self) -> bool:
        """
        True while a read_samples() or record_to_file() coroutine is active.

        Example
        -------
        ```python
            >>> async def blink():
            ...     while aa.is_recording:
            ...         led.toggle()
            ...         await asyncio.sleep_ms(200)
        ```
        """
        ...

    async def tone(self, freq_hz: float, duration_ms: int, fade_ms: int | None = None) -> None:
        """
        Play a sine-wave tone without blocking the event loop.

        :param freq_hz: Tone frequency in Hz. Use 0 for silence.
        :param duration_ms: Tone duration in milliseconds.
        :param fade_ms: Optional fade-in/out duration in milliseconds.

        Example
        -------
        ```python
            >>> async def main():
            ...     await asyncio.gather(aa.tone(440, 500), display_task())
        ```
        """
        ...

    async def note(
        self,
        seq: tuple | list,
        gap_ms: int | None = None,
        gap_ratio: float | None = None,
        fade_ms: int | None = None,
    ) -> None:
        """
        Play a (note, length, note, length, ...) sequence without blocking.

        :param seq: Alternating note-name and duration-denominator values.
        :param gap_ms: Fixed silence inserted after each played note.
        :param gap_ratio: Fraction of each note reserved as trailing silence.
        :param fade_ms: Optional fade duration in milliseconds.

        Example
        -------
        ```python
            >>> TETRIS = ('E5', 4, 'B4', 8, 'C5', 8, 'D5', 8, 'E5', 16)
            >>>
            >>> async def main():
            ...     await asyncio.gather(aa.note(TETRIS), button_task())
        ```
        """
        ...

    async def play_pcm16(self, data: bytes | bytearray | memoryview) -> None:
        """
        Play raw little-endian PCM16 mono data without blocking the event loop.

        :param data: Buffer containing signed 16-bit samples.

        Example
        -------
        ```python
            >>> async def main():
            ...     pcm = generate_pcm()
            ...     await asyncio.gather(aa.play_pcm16(pcm), ui_task())
        ```
        """
        ...

    async def play(self, wav_path: str) -> None:
        """
        Play a PCM WAV file without blocking the event loop.

        Supported formats: 8/16-bit PCM, mono or stereo (stereo mixed to mono).

        :param wav_path: Path to a WAV file on the device filesystem.
        :raises ValueError: If the WAV format is not supported.

        Example
        -------
        ```python
            >>> async def main():
            ...     await asyncio.gather(
            ...         aa.play('/res/come_get_it.wav'),
            ...         button_task(),
            ...     )
        ```
        """
        ...

    async def read_samples(self, duration_ms: int) -> bytearray:
        """
        Capture microphone audio and return PCM16 samples without blocking.

        :param duration_ms: Recording duration in milliseconds.
        :return: Bytearray of little-endian signed 16-bit samples.
        :raises MemoryError: If the required buffer cannot be allocated.

        Example
        -------
        ```python
            >>> async def main():
            ...     samples = await aa.read_samples(1000)
        ```
        """
        ...

    async def record_to_file(self, filename: str, duration_ms: int) -> None:
        """
        Record microphone audio to a WAV file without blocking the event loop.

        Yields to the event loop between RX retries (1 ms sleep) and after
        each file write chunk. The I2S bus is deinited before each flash
        write to prevent the RP2350 DMA + flash crash.

        :param filename: Output WAV file path.
        :param duration_ms: Recording duration in milliseconds.

        Example
        -------
        ```python
            >>> async def main():
            ...     await asyncio.gather(
            ...         aa.record_to_file('/rec.wav', 5000),
            ...         led_blink_task(),
            ...     )
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Deinitialize the underlying Audio instance.

        Example
        -------
        ```python
            >>> aa.deinit()
        ```
        """
        ...
