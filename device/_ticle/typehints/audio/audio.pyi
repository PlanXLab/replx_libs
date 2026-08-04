"""
Unified I2S audio input/output with TX/RX mode switching.

This module provides a single Audio class that can drive an I2S DAC for
audio output and an I2S microphone for audio input on RP2 boards. Because the
same I2S bus is reused for both directions, playback and recording are blocking
operations that switch the bus mode internally.

Features:
    - Tone and note-sequence playback
    - PCM16 and WAV playback
    - Raw microphone capture
    - Recording to PCM bytes or WAV file
    - Live input level monitoring

Examples:
    Basic playback:

    >>> from audio.audio import Audio
    >>> audio = Audio(sck=4, ws=5, sd_out=7, sd_in=6)
    >>> audio.tone(440, 300)
    >>> audio.note(('C5', 8, 'E5', 8, 'G5', 4))

    Recording and monitoring:

    >>> level = audio.get_level()
    >>> raw = audio.read_samples(500)
    >>> audio.record_to_file('/record.wav', 3000)
    >>> audio.deinit()

Note:
    - Playback and recording cannot run at the same time
    - On RP2, ws must be sck + 1 for machine.I2S
    - Default output/input format is mono
"""


class Audio:
    """
    Unified I2S audio controller with automatic TX/RX mode switching.

    The class manages a single RP2 I2S bus and reconfigures it for speaker
    output or microphone input as needed. This keeps the public API compact
    while matching the hardware constraint of sharing BCLK and WS.

    :param sck: I2S serial clock pin number.
    :param ws: I2S word-select pin number. Must be sck + 1 on RP2.
    :param sd_out: I2S TX data pin connected to the DAC input.
    :param sd_in: I2S RX data pin connected to the microphone output.
    :param tempo_bpm: Default tempo for note playback (20-300 BPM).
    :param default_fade_ms: Default fade-in/out duration for tones.
    :param default_volume: Default playback volume (0.0-1.0).
    :param default_mic_gain: Default microphone digital gain (0.0-256.0). 1.0 = no gain.
    :param rate: Default sample rate in Hz.
    :param ibuf: Internal I2S DMA buffer size in bytes.

    Example
    -------
    ```python
        >>> audio = Audio(sck=4, ws=5, sd_out=7, sd_in=6)
        >>> audio.volume = 0.25
        >>> audio.tone(523.25, 250)     # C5 for 250ms
        >>> audio.deinit()
    ```
    """

    def __init__(
        self,
        sck: int,
        ws: int,
        sd_out: int,
        sd_in: int,
        *,
        tempo_bpm: int = 120,
        default_fade_ms: int = 6,
        default_volume: float = 0.12,
        default_mic_gain: float = 16.0,
        rate: int = 16000,
        ibuf: int = 8192,
    ) -> None: ...

    def deinit(self) -> None:
        """
        Deinitialize the active I2S instance and release the bus.

        Example
        -------
        ```python
            >>> audio.deinit()
        ```
        """
        ...

    def standby(self) -> None:
        """
        Close the active I2S instance and park pins for quiet idle.

        The Audio object remains reusable. The next playback or recording
        call opens I2S again automatically. Public playback methods already
        write trailing silence before returning, so standby() can be called
        after playback without adding another tail delay. This is useful when
        Audio playback should be closed while no sound is being played.
        Automatic PIO allocation in Matrix/Effect prefers non-I2S state
        machines, so Audio can usually open lazily on the first playback.

        Example
        -------
        ```python
            >>> from ticle_lite.audio import Audio
            >>> from ticle_lite.ws2812 import Matrix
            >>>
            >>> audio = Audio(sck=4, ws=5, sd_out=7, sd_in=6)
            >>> matrix = Matrix([0])
            >>> audio.tone(880, 100)
            >>> audio.standby()
        ```
        """
        ...

    @property
    def tempo(self) -> int:
        """
        Current note-playback tempo in BPM.

        Example
        -------
        ```python
            >>> audio.tempo
            120
        ```
        """
        ...

    @tempo.setter
    def tempo(self, bpm: int) -> None:
        """
        Set note-playback tempo in BPM. Valid range is 20-300.

        Example
        -------
        ```python
            >>> audio.tempo = 96
            >>> audio.tempo = 144
        ```
        """
        ...

    @property
    def volume(self) -> float:
        """
        Current playback volume as a normalized value in range 0.0-1.0.

        Example
        -------
        ```python
            >>> audio.volume
            0.12
        ```
        """
        ...

    @volume.setter
    def volume(self, value: float) -> None:
        """
        Set playback volume. Valid range is 0.0-1.0.

        Example
        -------
        ```python
            >>> audio.volume = 0.1
            >>> audio.volume = 0.5
        ```
        """
        ...

    @property
    def mic_gain(self) -> float:
        """
        Current microphone digital gain (linear multiplier, Q8 internally).

        A value of 1.0 means no extra gain. Typical voice recordings on the
        ICS43434 mic require ~8-32 to reach a comfortable level. Values that
        exceed full scale are saturated to ±32767 to avoid wrap-around.

        Example
        -------
        ```python
            >>> audio.mic_gain
            16.0
        ```
        """
        ...

    @mic_gain.setter
    def mic_gain(self, value: float) -> None:
        """
        Set microphone digital gain. Valid range is 0.0-256.0.

        Example
        -------
        ```python
            >>> audio.mic_gain = 8.0      # quiet room speech
            >>> audio.mic_gain = 32.0     # distant speech
            >>> audio.mic_gain = 1.0      # bypass (raw level)
        ```
        """
        ...

    @property
    def rate(self) -> int:
        """
        Current active sample rate in Hz.

        Example
        -------
        ```python
            >>> audio.rate
            44100
        ```
        """
        ...

    @property
    def mode(self) -> str | None:
        """
        Current I2S mode: 'TX', 'RX', or None after deinit.

        Example
        -------
        ```python
            >>> audio.mode
            'TX'
        ```
        """
        ...

    def tone(self, freq_hz: float, duration_ms: int, fade_ms: int | None = None) -> None:
        """
        Play a sine-wave tone.

        :param freq_hz: Tone frequency in Hz. Use 0 for silence.
        :param duration_ms: Tone duration in milliseconds.
        :param fade_ms: Optional fade-in/out duration in milliseconds.

        Example
        -------
        ```python
            >>> audio.tone(440, 300)
            >>> audio.tone(880, 120, fade_ms=10)
            >>> audio.tone(0, 100)      # silence
        ```
        """
        ...

    def silence(self, duration_ms: int) -> None:
        """
        Write silence to the I2S TX stream without closing it.

        :param duration_ms: Silence duration in milliseconds.

        Use this to keep the speaker quiet while I2S remains open. Unlike
        tone(0, duration_ms), this method does not add an extra tail drain,
        so it is suitable for periodic idle keepalive writes.

        Example
        -------
        ```python
            >>> audio = Audio(sck=4, ws=5, sd_out=7, sd_in=6)
            >>> audio.silence(40)
            >>> audio.tone(880, 80)
            >>> audio.silence(40)
        ```
        """
        ...

    def note(
        self,
        seq: tuple | list,
        gap_ms: int | None = None,
        gap_ratio: float | None = None,
        fade_ms: int | None = None,
    ) -> None:
        """
        Play a flat (note, length, note, length, ...) note sequence.

        :param seq: Alternating note-name and duration-denominator values.
        :param gap_ms: Fixed silence inserted after each played note.
        :param gap_ratio: Fraction of each note reserved as trailing silence.
        :param fade_ms: Optional fade duration in milliseconds.

        Example
        -------
        ```python
            >>> melody = ('C5', 8, 'E5', 8, 'G5', 4, 'R', 8, 'C6', 4)
            >>> audio.note(melody)
            >>> audio.note(melody, gap_ms=20, fade_ms=8)
        ```
        """
        ...

    def play_pcm16(self, data: bytes | bytearray | memoryview, *, dither: bool = False) -> None:
        """
        Play raw little-endian PCM16 mono audio data.

        :param data: Byte-oriented buffer containing signed 16-bit samples.

        Example
        -------
        ```python
            >>> pcm = bytearray(512)
            >>> audio.play_pcm16(pcm)
        ```
        """
        ...

    def play(self, wav_path: str, *, resample: bool = False) -> None:
        """
        Play a PCM WAV file.

        Supported input formats are 8-bit or 16-bit PCM, mono or stereo.
        Stereo input is mixed down to mono.

        :param wav_path: Path to a WAV file on the device filesystem.
        :raises ValueError: If the WAV file is not supported.

        Example
        -------
        ```python
            >>> audio.play('/res/doorbell.wav')
        ```
        """
        ...

    def read_raw(
        self,
        buffer: bytearray | memoryview | None = None,
        num_frames: int | None = None,
    ) -> int:
        """
        Read raw 32-bit microphone frames into a buffer.

        :param buffer: Destination buffer. If None, an internal buffer is used.
        :param num_frames: Number of mono frames to read. Defaults to buffer size.
        :return: Number of bytes read.

        Example
        -------
        ```python
            >>> buf = bytearray(1024)
            >>> n = audio.read_raw(buf, num_frames=256)
            >>> print(n)
        ```
        """
        ...

    def read_samples(self, duration_ms: int) -> bytearray:
        """
        Record audio and return PCM16 mono samples.

        :param duration_ms: Recording duration in milliseconds.
        :return: Bytearray of little-endian signed 16-bit samples.

        Example
        -------
        ```python
            >>> samples = audio.read_samples(1000)
            >>> print(len(samples))
        ```
        """
        ...

    def record_to_file(self, filename: str, duration_ms: int) -> None:
        """
        Record audio directly to a WAV file.

        Captures into a small, fixed-size staging buffer and flushes it to flash
        periodically rather than buffering the whole recording in RAM, so
        recording duration is limited by flash space rather than available heap.
        The I2S input is briefly closed and reopened around each flash write
        (a flash write disables interrupts, which would otherwise corrupt an
        actively-running I2S/DMA session), causing a small gap in the captured
        audio at each flush boundary.

        :param filename: Output WAV file path.
        :param duration_ms: Recording duration in milliseconds.

        Example
        -------
        ```python
            >>> audio.record_to_file('/record.wav', 3000)
        ```
        """
        ...

    def get_level(self) -> float:
        """
        Measure current microphone monitoring level.

        The level is computed from DC-removed RMS energy of the raw 32-bit I2S
        input and then mapped from a practical dBFS range into 0.0-1.0 for UI
        bars, thresholding, and simple activity monitoring.

        :return: Normalized input level in range 0.0-1.0.

        Example
        -------
        ```python
            >>> level = audio.get_level()
            >>> print(level)
        ```
        """
        ...

    def is_sound_detected(self, threshold: float = 0.01) -> bool:
        """
        Check whether current sound level exceeds a threshold.

        :param threshold: Detection threshold in range 0.0-1.0.
        :return: True if input level is at least the threshold.

        Example
        -------
        ```python
            >>> if audio.is_sound_detected(0.05):
            ...     print('sound detected')
        ```
        """
        ...

    def rms(self, num_frames: int | None = None, buffer: bytearray | memoryview | None = None) -> int:
        """
        Read microphone input and return the RMS amplitude.

        Calls ``read_raw()`` internally so the caller does not need a separate
        buffer or an explicit ``read_raw()`` call. The RMS is computed from the
        upper 16 bits of each 32-bit I2S frame (signed PCM).

        :param num_frames: Number of mono frames to capture. Defaults to the
            internal stream buffer size (~46 ms at 44100 Hz).
        :param buffer: Optional external buffer (bytearray or memoryview).
            Must be at least ``num_frames * 4`` bytes. If None, the internal
            stream buffer is used.
        :return: Integer RMS value in the range 0-32767.

        Example
        -------
        ```python
            >>> level = audio.rms(441)           # ~10 ms snapshot
            >>> if audio.rms(441) > 1500:
            ...     print('clap!')
        ```
        """
        ...