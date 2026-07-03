# @package: audio_async
# @version: 1.1.0
# @type: device-specific
# @category: audio
# @interface: I2S
# @depends: audio
# @platforms: rp2
# @tags: audio, i2s, wav, tone, note, record, async, asyncio
# @author: PlanXLab Development Team

import asyncio
from ticle_lite.audio import Audio


class _AsyncI2SWriter:
    def __init__(self, i2s):
        self._i2s = i2s

    def write_sync(self, data):
        """Synchronous write without yielding. Use inside a batch loop."""
        self._i2s.write(data)

    async def awrite(self, data):
        """Write then yield once. Use for gap/drain silence only."""
        self._i2s.write(data)
        await asyncio.sleep_ms(0)


class AsyncAudio:
    def __init__(self, audio):
        self._audio = audio
        self._playing = False
        self._recording = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._audio.deinit()

    @property
    def audio(self):
        return self._audio

    @property
    def is_playing(self):
        return self._playing

    @property
    def is_recording(self):
        return self._recording

    async def _rest_async(self, swriter, ms):
        # Write silence in ibuf-sized batches to keep DMA fed;
        # yield once per full DMA-buffer-worth so other tasks can run.
        a = self._audio
        ms = int(ms)
        if ms <= 0:
            return
        total_bytes = int(a._rate * ms / 1000.0 + 0.5) * 2
        if total_bytes <= 0:
            return
        left = total_bytes
        z_mv = a._silence_buf
        z_len = len(z_mv)
        ibuf_bytes = a._ibuf
        batch = 0
        while left > 0:
            take = z_len if left > z_len else left
            swriter.write_sync(z_mv[:take])
            left -= take
            batch += take
            if batch >= ibuf_bytes:
                await asyncio.sleep_ms(0)
                batch = 0
        if batch > 0:
            await asyncio.sleep_ms(0)

    async def _play_sine_async(self, swriter, freq_hz, duration_ms, fade_ms):
        # Write sine chunks synchronously in ibuf-frame batches.
        # Yield only once per full DMA buffer to prevent underrun while
        # still allowing other tasks to run during long notes.
        a = self._audio
        if freq_hz <= 0.0 or duration_ms <= 0:
            await self._rest_async(swriter, duration_ms)
            return

        amp_q15 = a._vol_to_q15(a._vol)
        total_samples = int(a._rate * duration_ms / 1000.0 + 0.5)
        fade_samples = max(1, int(a._rate * fade_ms / 1000.0 + 0.5))
        if fade_samples * 2 > total_samples:
            fade_samples = max(1, total_samples // 2)

        shift = 32 - a._SINE_BITS
        frac_bits = a._SINE_FRAC_BITS
        frac_mask = (1 << frac_bits) - 1
        idx_mask = (1 << a._SINE_BITS) - 1
        phase = 0
        step = int((freq_hz * (1 << 32)) / a._rate)
        sent = 0
        ibuf_frames = a._ibuf // 2   # frames that fill the DMA ring buffer
        batch = 0
        while sent < total_samples:
            todo = min(a._TONE_CHUNK_FRAMES, total_samples - sent)
            phase = a._render_sine_chunk(
                todo, sent, total_samples, fade_samples, amp_q15,
                phase, step, shift,
                a._sine_table, a._tone_buf, a._fade_curve,
                a._FADE_TABLE_SIZE, a._SINE_BIAS,
                frac_bits, frac_mask, idx_mask,
            )
            swriter.write_sync(a._tone_mv[:todo * 2])
            sent += todo
            batch += todo
            if batch >= ibuf_frames:
                await asyncio.sleep_ms(0)   # yield after every full DMA buffer
                batch = 0
        if batch > 0:
            await asyncio.sleep_ms(0)       # final yield

    async def _drain_tail_async(self, swriter):
        a = self._audio
        tail_ms = (a._ibuf * 1000) // (2 * a._rate) + a._TAIL_MARGIN_MS
        await self._rest_async(swriter, tail_ms)

    async def _read_raw_async(self, target, n_bytes):
        a = self._audio
        bytes_read = 0
        while bytes_read < n_bytes:
            n = a._i2s.readinto(target[bytes_read:])
            if n:
                bytes_read += n
            else:
                await asyncio.sleep_ms(1)
        return bytes_read

    async def tone(self, freq_hz, duration_ms, fade_ms=None):
        a = self._audio
        duration_ms = max(0, int(duration_ms))
        fade = a._fade if fade_ms is None else max(0, int(fade_ms))
        qf = Audio._quantize_freq(freq_hz, a._rate)
        self._playing = True
        try:
            if qf <= 0.0:
                if a._mode == a._MODE_TX and a._i2s is not None:
                    swriter = _AsyncI2SWriter(a._i2s)
                    await self._rest_async(swriter, duration_ms)
                    await self._drain_tail_async(swriter)
            else:
                a._ensure_tx_mode()
                swriter = _AsyncI2SWriter(a._i2s)
                await self._play_sine_async(swriter, qf, duration_ms, fade)
                await self._drain_tail_async(swriter)
        finally:
            self._playing = False

    async def note(self, seq, gap_ms=None, gap_ratio=None, fade_ms=None):
        a = self._audio
        a._ensure_tx_mode()
        if len(seq) % 2 != 0:
            raise ValueError('Invalid (note, length) pairs')

        fade = a._fade if fade_ms is None else max(0, int(fade_ms))
        gap_r = a._gap_ratio if gap_ratio is None else float(gap_ratio)
        if gap_r < 0.0 or gap_r >= 1.0:
            raise ValueError('gap_ratio must be in range 0.0 <= x < 1.0')
        fixed_gap = None if gap_ms is None else max(0, int(gap_ms))

        swriter = _AsyncI2SWriter(a._i2s)
        self._playing = True
        try:
            i = 0
            while i < len(seq):
                name = seq[i]
                denom = seq[i + 1]
                i += 2

                dur_ms = a._note_duration_ms(denom)
                freq = Audio._note_to_freq(name)

                if freq <= 0.0:
                    await self._rest_async(swriter, dur_ms)
                    continue

                if fixed_gap is not None:
                    gap = min(fixed_gap, dur_ms)
                    play_ms = max(0, dur_ms - gap)
                else:
                    play_ms = int(dur_ms * (1.0 - gap_r) + 0.5)
                    gap = max(0, dur_ms - play_ms)

                if play_ms > 0:
                    qf = Audio._quantize_freq(freq, a._rate)
                    await self._play_sine_async(swriter, qf, play_ms, fade)
                if gap > 0:
                    await self._rest_async(swriter, gap)

            await self._drain_tail_async(swriter)
        finally:
            self._playing = False

    async def play_pcm16(self, data):
        a = self._audio
        a._ensure_tx_mode()
        mv_in = data if isinstance(data, memoryview) else memoryview(data)
        n = len(mv_in) & ~1
        if n <= 0:
            return
        vol = a._get_validated_volume()
        if vol <= 0.0:
            return

        swriter = _AsyncI2SWriter(a._i2s)
        self._playing = True
        try:
            if abs(vol - 1.0) < 1e-6:
                await swriter.awrite(mv_in[:n])
            else:
                vol_q15 = a._vol_to_q15(vol)
                tmp = a._pcm_buf
                tmp_mv = a._pcm_mv
                cap = len(tmp) & ~1
                off = 0
                while off < n:
                    take = min(cap, n - off) & ~1
                    if take <= 0:
                        break
                    tmp_mv[:take] = mv_in[off:off + take]
                    a._dither_idx = a._apply_vol_pcm16(
                        tmp, take, vol_q15, 0,
                        a._dither_noise, a._dither_idx, a._DITHER_MASK,
                    )
                    await swriter.awrite(tmp_mv[:take])
                    off += take
            await self._drain_tail_async(swriter)
        finally:
            self._playing = False

    async def play(self, wav_path):
        a = self._audio
        vol = a._get_validated_volume()
        if vol <= 0.0:
            return

        default_rate = a._default_rate

        with open(wav_path, 'rb') as f:
            audio_fmt, num_ch, src_rate, bits_per, data_size = a._read_wav_header(f)

            if audio_fmt != 1 or bits_per not in (8, 16):
                raise ValueError('WAV: only PCM 8/16-bit supported')
            if num_ch not in (1, 2):
                raise ValueError('WAV: only mono/stereo supported')

            a._ensure_tx_mode(rate=src_rate)
            swriter = _AsyncI2SWriter(a._i2s)
            bytes_per_frame_in = (bits_per // 8) * num_ch
            vol_q15 = a._vol_to_q15(vol)

            self._playing = True
            try:
                remain = data_size
                while remain > 0:
                    to_read = min(remain, len(a._wav_in_buf))
                    to_read -= to_read % bytes_per_frame_in
                    if to_read <= 0:
                        break

                    read_n = f.readinto(a._wav_in_mv[:to_read])
                    if not read_n:
                        break
                    remain -= read_n

                    read_n -= read_n % bytes_per_frame_in
                    if read_n <= 0:
                        break

                    n_frames = read_n // bytes_per_frame_in
                    if bits_per == 8 and num_ch == 1:
                        out_n = a._convert_wav_8mono(a._wav_in_buf, a._wav_out_buf, n_frames, vol_q15)
                    elif bits_per == 8 and num_ch == 2:
                        out_n = a._convert_wav_8stereo(a._wav_in_buf, a._wav_out_buf, n_frames, vol_q15)
                    elif bits_per == 16 and num_ch == 1:
                        out_n = a._convert_wav_16mono(a._wav_in_buf, a._wav_out_buf, n_frames, vol_q15)
                    else:
                        out_n = a._convert_wav_16stereo(a._wav_in_buf, a._wav_out_buf, n_frames, vol_q15)

                    if out_n > 0:
                        await swriter.awrite(a._wav_out_mv[:out_n])

                await self._drain_tail_async(swriter)
            finally:
                self._playing = False

        if a._rate != default_rate:
            a._ensure_tx_mode(rate=default_rate)

    async def read_samples(self, duration_ms):
        a = self._audio
        a._ensure_rx_mode()

        total_frames = int(a._rate * int(duration_ms) / 1000.0 + 0.5)
        required_bytes = total_frames * 2
        try:
            output = bytearray(required_bytes)
        except MemoryError:
            raise MemoryError('Could not allocate recording buffer; use record_to_file() for long recordings')
        output_mv = memoryview(output)

        self._recording = True
        try:
            frames_read = 0
            out_off = 0
            while frames_read < total_frames:
                frames_to_read = min(a._REC_BUFFER_FRAMES, total_frames - frames_read)
                br = await self._read_raw_async(a._rec_mv, frames_to_read * 4)
                actual_frames = br // 4
                bc = a._convert_32to16(a._rec_buf, a._convert_buf, actual_frames)
                output_mv[out_off:out_off + bc] = a._convert_mv[:bc]
                out_off += bc
                frames_read += actual_frames
        finally:
            self._recording = False

        return output

    async def record_to_file(self, filename, duration_ms):
        a = self._audio
        total_frames = int(a._rate * int(duration_ms) / 1000.0 + 0.5)
        data_size = total_frames * 2

        with open(filename, 'wb') as f:
            a._write_wav_header(f, a._rate, data_size)
            try:
                f.flush()
            except Exception:
                pass

        chunk_bytes = a._REC_FILE_CHUNK_BYTES
        chunk_frames = chunk_bytes // 2
        if chunk_frames < a._REC_BUFFER_FRAMES:
            chunk_frames = a._REC_BUFFER_FRAMES
            chunk_bytes = chunk_frames * 2

        try:
            ram_buf = bytearray(chunk_bytes)
        except MemoryError:
            chunk_frames = a._REC_BUFFER_FRAMES
            chunk_bytes = chunk_frames * 2
            ram_buf = bytearray(chunk_bytes)
        ram_mv = memoryview(ram_buf)

        self._recording = True
        try:
            with open(filename, 'r+b') as f:
                f.seek(44)
                frames_done = 0
                while frames_done < total_frames:
                    take_frames = min(chunk_frames, total_frames - frames_done)

                    a._ensure_rx_mode()
                    out_off = 0
                    captured = 0
                    while captured < take_frames:
                        sub = min(a._REC_BUFFER_FRAMES, take_frames - captured)
                        br = await self._read_raw_async(a._rec_mv, sub * 4)
                        af = br // 4
                        if af <= 0:
                            continue
                        bc = a._convert_32to16(a._rec_buf, a._convert_buf, af)
                        ram_mv[out_off:out_off + bc] = a._convert_mv[:bc]
                        out_off += bc
                        captured += af

                    if a._i2s is not None:
                        a._i2s.deinit()
                        a._i2s = None
                    a._mode = None
                    a._idle_i2s_pins()

                    f.write(bytes(ram_mv[:out_off]))
                    await asyncio.sleep_ms(0)
                    frames_done += captured
        finally:
            self._recording = False
            if a._i2s is not None:
                a._i2s.deinit()
                a._i2s = None
            a._mode = None
            a._idle_i2s_pins()

    def deinit(self):
        self._audio.deinit()
