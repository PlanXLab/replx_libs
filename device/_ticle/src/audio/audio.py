# @package: audio
# @version: 1.9
# @type: device-specific
# @category: audio
# @interface: I2S
# @depends: machine
# @platforms: rp2
# @tags: audio, i2s, microphone, speaker, wav, pcm, tone
# @author: PlanXLab Development Team

import math
import struct
import time
import gc
from array import array
from random import getrandbits

import micropython
from machine import I2S, Pin
from uctypes import addressof


class Audio:
    _MODE_TX = 'TX'
    _MODE_RX = 'RX'

    _DEFAULT_RATE = 16000
    _DEFAULT_IBUF = 4096
    _REC_FILE_CHUNK_BYTES = 32768
    _FORMAT = I2S.MONO

    _TX_BITS = 16
    _RX_BITS = 32

    _TONE_CHUNK_FRAMES = 1024
    _PCM_BUFFER_FRAMES = 1024
    _WAV_BUFFER_FRAMES = 1024
    _REC_BUFFER_FRAMES = 1024
    _STREAM_BUFFER_FRAMES = 512
    _SILENCE_BUFFER_SIZE = 2048

    _MODE_SETTLE_MS = 100
    _TX_PRIME_MS = 80
    _TAIL_MARGIN_MS = 12
    _LEVEL_FLOOR_DB = -60.0
    _LEVEL_WINDOW_MS = 100
    _LEVEL_RELEASE_MS = 450
    _LEVEL_RMS_CHUNK = 256
    _LEVEL_VAR_SHIFT = 10

    _SINE_BITS = 10
    _SINE_FRAC_BITS = 8
    _SINE_BIAS = 32768
    _FADE_TABLE_SIZE = 256
    _DITHER_TABLE_SIZE = 512
    _DITHER_MASK = 511

    _Q15_MAX = 32767

    _DEFAULT_MIC_GAIN = 16.0
    _MIC_GAIN_MAX = 256.0
    _MIC_GAIN_Q8_MAX = 65535

    def __init__(
        self,
        sck,
        ws,
        sd_out,
        sd_in,
        *,
        tempo_bpm=120,
        default_fade_ms=6,
        default_volume=0.12,
        default_mic_gain=_DEFAULT_MIC_GAIN,
        rate=_DEFAULT_RATE,
        ibuf=_DEFAULT_IBUF,
    ):
        sck = int(sck)
        ws = int(ws)
        sd_out = int(sd_out)
        sd_in = int(sd_in)

        if ws != sck + 1:
            raise ValueError('On RP2 I2S, ws must be sck + 1')
        if sd_out == sd_in:
            raise ValueError('sd_out and sd_in must be different pins')

        self._pin_sck = sck
        self._pin_ws = ws
        self._pin_sd_out = sd_out
        self._pin_sd_in = sd_in

        self._i2s_id = 0
        self._ibuf = max(1024, int(ibuf))
        self._default_rate = max(4000, int(rate))
        self._rate = self._default_rate
        self._tempo = 120
        self._fade = max(0, int(default_fade_ms))
        self._vol = 0.12
        self._gap_ratio = 0.08

        self.tempo = tempo_bpm
        self.volume = default_volume
        self._mic_gain_q8 = 256
        self.mic_gain = default_mic_gain

        self._i2s = None
        self._mode = None

        self._fmt = self._FORMAT
        self._channels = 1 if self._fmt == I2S.MONO else 2

        self._tone_buf = bytearray(self._TONE_CHUNK_FRAMES * 2)
        self._tone_mv = memoryview(self._tone_buf)

        self._silence_buf = memoryview(bytearray(self._SILENCE_BUFFER_SIZE))

        self._pcm_buf = None
        self._pcm_mv = None

        self._wav_in_buf = None
        self._wav_in_mv = None
        self._wav_out_buf = None
        self._wav_out_mv = None

        self._rec_buf = None
        self._rec_mv = None

        meter_frames = int(self._rate * self._LEVEL_WINDOW_MS / 1000.0 + 0.5)
        ibuf_frames = max(256, self._ibuf // 4)
        self._stream_frames = max(256, min(ibuf_frames, max(self._STREAM_BUFFER_FRAMES, meter_frames)))

        self._stream_buf = None
        self._stream_mv = None

        self._level_state = 0.0
        self._level_last_ms = time.ticks_ms()

        self._convert_buf = None
        self._convert_mv = None

        n = 1 << self._SINE_BITS
        tbl = array('H', [0] * n)
        bias = self._SINE_BIAS
        for i in range(n):
            angle = 2.0 * math.pi * i / n
            tbl[i] = (int(round(math.sin(angle) * self._Q15_MAX)) + bias) & 0xFFFF
        self._sine_table = tbl

        fade_n = self._FADE_TABLE_SIZE
        fade_tbl = array('H', [0] * fade_n)
        for i in range(fade_n):
            fade_tbl[i] = int(round((1.0 - math.cos(math.pi * i / fade_n)) * 0.5 * self._Q15_MAX))
        self._fade_curve = fade_tbl

        dn = self._DITHER_TABLE_SIZE
        dnoise = array('B', [0] * dn)
        for i in range(dn):
            dnoise[i] = (getrandbits(1) - getrandbits(1)) + 1
        self._dither_noise = dnoise
        self._dither_idx = 0

        self._resample_buf = None
        self._resample_mv = None

    def _open_i2s(self, mode_name, rate):
        if mode_name == self._MODE_TX:
            sd_pin = self._pin_sd_out
            bits = self._TX_BITS
            mode = I2S.TX
        else:
            sd_pin = self._pin_sd_in
            bits = self._RX_BITS
            mode = I2S.RX

        gc.collect()
        try:
            self._i2s = I2S(
                self._i2s_id,
                sck=Pin(self._pin_sck),
                ws=Pin(self._pin_ws),
                sd=Pin(sd_pin),
                mode=mode,
                bits=bits,
                format=self._fmt,
                rate=rate,
                ibuf=self._ibuf,
            )
        except MemoryError:
            gc.collect()
            self._i2s = I2S(
                self._i2s_id,
                sck=Pin(self._pin_sck),
                ws=Pin(self._pin_ws),
                sd=Pin(sd_pin),
                mode=mode,
                bits=bits,
                format=self._fmt,
                rate=rate,
                ibuf=self._ibuf,
            )
        self._mode = mode_name
        self._rate = int(rate)
        if mode_name == self._MODE_TX:
            self._rest_ms(self._TX_PRIME_MS)
        else:
            time.sleep_ms(self._MODE_SETTLE_MS)

    def _idle_i2s_pins(self):
        Pin(self._pin_sck, Pin.OUT, value=0)
        Pin(self._pin_ws, Pin.OUT, value=0)
        Pin(self._pin_sd_out, Pin.OUT, value=0)
        Pin(self._pin_sd_in, Pin.IN)

    def _ensure_tx_mode(self, rate=None):
        target_rate = self._rate if rate is None else max(4000, int(rate))
        if self._mode == self._MODE_TX and self._i2s is not None and self._rate == target_rate:
            return

        if self._mode == self._MODE_TX and self._i2s is not None:
            self._drain_tail()

        if self._i2s is not None:
            self._i2s.deinit()
            self._i2s = None

        self._idle_i2s_pins()

        self._open_i2s(self._MODE_TX, target_rate)

    def _ensure_rx_mode(self):
        if self._mode == self._MODE_RX and self._i2s is not None:
            return

        if self._mode == self._MODE_TX and self._i2s is not None:
            self._drain_tail()

        if self._i2s is not None:
            self._i2s.deinit()
            self._i2s = None

        self._idle_i2s_pins()

        self._open_i2s(self._MODE_RX, self._rate)

    def deinit(self):
        if self._mode == self._MODE_TX and self._i2s is not None:
            try:
                self._drain_tail(tail_margin_ms=8)
            except Exception:
                pass

        if self._i2s is not None:
            self._i2s.deinit()
            self._i2s = None

        self._idle_i2s_pins()

        self._mode = None

    def standby(self):
        if self._i2s is not None:
            self._i2s.deinit()
            self._i2s = None

        self._idle_i2s_pins()

        self._mode = None

    @property
    def tempo(self):
        return self._tempo

    @tempo.setter
    def tempo(self, bpm):
        bpm = int(bpm)
        if bpm < 20 or bpm > 300:
            raise ValueError('Tempo must be 20-300 BPM')
        self._tempo = bpm

    @property
    def volume(self):
        return self._vol

    @volume.setter
    def volume(self, value):
        value = float(value)
        if value < 0.0 or value > 1.0:
            raise ValueError('Volume must be 0.0-1.0')
        self._vol = value

    @property
    def mic_gain(self):
        return self._mic_gain_q8 / 256.0

    @mic_gain.setter
    def mic_gain(self, value):
        value = float(value)
        if value < 0.0:
            raise ValueError('mic_gain must be >= 0.0')
        if value > self._MIC_GAIN_MAX:
            value = self._MIC_GAIN_MAX
        q8 = int(round(value * 256.0))
        if q8 < 0:
            q8 = 0
        if q8 > self._MIC_GAIN_Q8_MAX:
            q8 = self._MIC_GAIN_Q8_MAX
        self._mic_gain_q8 = q8

    @property
    def rate(self):
        return self._rate

    @property
    def mode(self):
        return self._mode

    @staticmethod
    def _quantize_freq(freq_hz, rate):
        freq_hz = float(freq_hz)
        if freq_hz <= 0.0:
            return 0.0
        period = max(4, int(round(rate / freq_hz)))
        return rate / period

    def tone(self, freq_hz, duration_ms, fade_ms=None):
        duration_ms = max(0, int(duration_ms))
        fade = self._fade if fade_ms is None else max(0, int(fade_ms))
        qf = self._quantize_freq(freq_hz, self._rate)

        if qf <= 0.0:
            if self._mode == self._MODE_TX and self._i2s is not None:
                self._rest_ms(duration_ms)
                self._drain_tail(tail_margin_ms=8)
            return

        self._ensure_tx_mode()
        self._play_sine(qf, duration_ms, fade)
        self._drain_tail(tail_margin_ms=8)

    def silence(self, duration_ms):
        self._ensure_tx_mode()
        self._rest_ms(duration_ms)

    @staticmethod
    def _note_to_freq(name):
        u = str(name).strip().upper()
        if u in ('REST', 'R'):
            return 0.0
        if not u:
            raise ValueError('Empty note name')

        note = u[0]
        if note not in ('A', 'B', 'C', 'D', 'E', 'F', 'G'):
            raise ValueError('Invalid note name: %s' % name)

        i = 1
        acc = 0
        if i < len(u) and u[i] in ('#', 'S'):
            acc = 1
            i += 1
        elif i < len(u) and u[i] == 'B':
            acc = -1
            i += 1

        try:
            octave = int(u[i:])
        except ValueError:
            raise ValueError('Invalid note octave: %s' % name)

        semis = {'C': -9, 'D': -7, 'E': -5, 'F': -4, 'G': -2, 'A': 0, 'B': 2}
        n = semis[note] + acc + 12 * (octave - 4)
        return 440.0 * (2.0 ** (n / 12.0))

    def note(self, seq, gap_ms=None, gap_ratio=None, fade_ms=None):
        self._ensure_tx_mode()

        if len(seq) % 2 != 0:
            raise ValueError('Invalid (note, length) pairs')

        fade = self._fade if fade_ms is None else max(0, int(fade_ms))
        gap_r = self._gap_ratio if gap_ratio is None else float(gap_ratio)
        if gap_r < 0.0 or gap_r >= 1.0:
            raise ValueError('gap_ratio must be in range 0.0 <= x < 1.0')

        fixed_gap = None if gap_ms is None else max(0, int(gap_ms))

        i = 0
        while i < len(seq):
            name = seq[i]
            denom = seq[i + 1]
            i += 2

            dur_ms = self._note_duration_ms(denom)
            freq = self._note_to_freq(name)

            if freq <= 0.0:
                self._rest_ms(dur_ms)
                continue

            if fixed_gap is not None:
                gap = min(fixed_gap, dur_ms)
                play_ms = max(0, dur_ms - gap)
            else:
                play_ms = int(dur_ms * (1.0 - gap_r) + 0.5)
                gap = max(0, dur_ms - play_ms)

            if play_ms > 0:
                self._play_sine(freq, play_ms, fade)
            if gap > 0:
                self._rest_ms(gap)

        self._drain_tail(tail_margin_ms=8)

    def _get_validated_volume(self):
        return min(1.0, max(0.0, float(self._vol)))

    def _ensure_pcm_buf(self):
        if self._pcm_buf is None:
            self._pcm_buf = bytearray(self._PCM_BUFFER_FRAMES * 2)
            self._pcm_mv = memoryview(self._pcm_buf)

    def _ensure_wav_bufs(self):
        if self._wav_in_buf is None:
            self._wav_in_buf = bytearray(self._WAV_BUFFER_FRAMES * 4)
            self._wav_in_mv = memoryview(self._wav_in_buf)
        if self._wav_out_buf is None:
            self._wav_out_buf = bytearray(self._WAV_BUFFER_FRAMES * 2)
            self._wav_out_mv = memoryview(self._wav_out_buf)

    def _ensure_convert_buf(self, frames):
        needed = max(1, int(frames)) * 2
        if self._convert_buf is None or len(self._convert_buf) < needed:
            self._convert_buf = bytearray(needed)
            self._convert_mv = memoryview(self._convert_buf)

    def _ensure_rec_bufs(self):
        if self._rec_buf is None:
            self._rec_buf = bytearray(self._REC_BUFFER_FRAMES * 4)
            self._rec_mv = memoryview(self._rec_buf)
        self._ensure_convert_buf(self._REC_BUFFER_FRAMES)

    def _ensure_stream_bufs(self):
        if self._stream_buf is None:
            self._stream_buf = bytearray(self._stream_frames * 4)
            self._stream_mv = memoryview(self._stream_buf)
        self._ensure_convert_buf(self._stream_frames)

    def _vol_to_q15(self, vol):
        return int(self._Q15_MAX * vol)

    def play_pcm16(self, data, *, dither=False):
        self._ensure_tx_mode()

        mv_in = data if isinstance(data, memoryview) else memoryview(data)
        n = len(mv_in) & ~1
        if n <= 0:
            return

        vol = self._get_validated_volume()
        if vol <= 0.0:
            return

        if abs(vol - 1.0) < 1e-6 and not dither:
            self._write_all(mv_in[:n])
            self._drain_tail(tail_margin_ms=8)
            return

        self._ensure_pcm_buf()
        vol_q15 = self._vol_to_q15(vol)
        tmp = self._pcm_buf
        tmp_mv = self._pcm_mv
        cap = len(tmp) & ~1

        off = 0
        while off < n:
            take = min(cap, n - off)
            take &= ~1
            if take <= 0:
                break

            tmp_mv[:take] = mv_in[off:off + take]
            self._dither_idx = self._apply_vol_pcm16(
                tmp,
                take,
                vol_q15,
                1 if dither else 0,
                self._dither_noise,
                self._dither_idx,
                self._DITHER_MASK,
            )
            self._write_all(tmp_mv[:take])
            off += take

        self._drain_tail(tail_margin_ms=8)

    @staticmethod
    def _read_u32(f):
        b = f.read(4)
        if not b or len(b) < 4:
            raise ValueError('WAV: unexpected EOF')
        return struct.unpack('<I', b)[0]

    @staticmethod
    def _read_u16(f):
        b = f.read(2)
        if not b or len(b) < 2:
            raise ValueError('WAV: unexpected EOF')
        return struct.unpack('<H', b)[0]

    @staticmethod
    def _skip_chunk(f, size):
        while size > 0:
            take = 256 if size > 256 else size
            if len(f.read(take)) != take:
                raise ValueError('WAV: unexpected EOF while skipping chunk')
            size -= take

    def _read_wav_header(self, f):
        if f.read(4) != b'RIFF':
            raise ValueError('WAV: not RIFF')
        self._read_u32(f)
        if f.read(4) != b'WAVE':
            raise ValueError('WAV: not WAVE')

        audio_fmt = None
        num_ch = None
        src_rate = None
        bits_per = None

        while True:
            chunk_id = f.read(4)
            if not chunk_id or len(chunk_id) < 4:
                raise ValueError('WAV: data chunk not found')

            chunk_size = self._read_u32(f)

            if chunk_id == b'fmt ':
                fmt_data = f.read(chunk_size)
                if len(fmt_data) < 16:
                    raise ValueError('WAV: invalid fmt chunk')
                audio_fmt, num_ch, src_rate, _, _, bits_per = struct.unpack('<HHIIHH', fmt_data[:16])
                if chunk_size & 1:
                    self._skip_chunk(f, 1)
            elif chunk_id == b'data':
                if audio_fmt is None:
                    raise ValueError('WAV: fmt chunk must come before data')
                return audio_fmt, num_ch, src_rate, bits_per, chunk_size
            else:
                self._skip_chunk(f, chunk_size)
                if chunk_size & 1:
                    self._skip_chunk(f, 1)

    def play(self, wav_path, *, resample=False):
        vol = self._get_validated_volume()
        if vol <= 0.0:
            return

        default_rate = self._default_rate

        with open(wav_path, 'rb') as f:
            audio_fmt, num_ch, src_rate, bits_per, data_size = self._read_wav_header(f)

            if audio_fmt != 1 or bits_per not in (8, 16):
                raise ValueError('WAV: only PCM 8/16-bit supported')
            if num_ch not in (1, 2):
                raise ValueError('WAV: only mono/stereo supported')

            do_resample = resample and src_rate != default_rate
            play_rate = default_rate if do_resample else src_rate
            self._ensure_tx_mode(rate=play_rate)
            self._ensure_wav_bufs()

            bytes_per_sample_in = bits_per // 8
            bytes_per_frame_in = bytes_per_sample_in * num_ch
            vol_q15 = self._vol_to_q15(vol)

            if do_resample:
                self._ensure_resample_buf(src_rate, default_rate)
                src_step_q16 = (src_rate << 16) // default_rate
                acc_local = 0
            else:
                src_step_q16 = 0
                acc_local = 0

            remain = data_size
            while remain > 0:
                to_read = min(remain, self._WAV_BUFFER_FRAMES * bytes_per_frame_in)
                to_read -= to_read % bytes_per_frame_in
                if to_read <= 0:
                    break

                read_n = f.readinto(self._wav_in_mv[:to_read])
                if not read_n:
                    break
                remain -= read_n

                read_n -= read_n % bytes_per_frame_in
                if read_n <= 0:
                    break

                n_frames = read_n // bytes_per_frame_in
                if bits_per == 8 and num_ch == 1:
                    out_n = self._convert_wav_8mono(self._wav_in_buf, self._wav_out_buf, n_frames, vol_q15)
                elif bits_per == 8 and num_ch == 2:
                    out_n = self._convert_wav_8stereo(self._wav_in_buf, self._wav_out_buf, n_frames, vol_q15)
                elif bits_per == 16 and num_ch == 1:
                    out_n = self._convert_wav_16mono(self._wav_in_buf, self._wav_out_buf, n_frames, vol_q15)
                else:
                    out_n = self._convert_wav_16stereo(self._wav_in_buf, self._wav_out_buf, n_frames, vol_q15)

                if out_n <= 0:
                    continue

                if do_resample:
                    src_frames_chunk = out_n >> 1
                    chunk_end_q16 = src_frames_chunk << 16
                    if acc_local >= chunk_end_q16:
                        acc_local -= chunk_end_q16
                        continue
                    dst_n = (chunk_end_q16 - acc_local - 1) // src_step_q16 + 1
                    cap_n = len(self._resample_buf) >> 1
                    if dst_n > cap_n:
                        dst_n = cap_n
                    self._resample_nn_16(
                        self._wav_out_buf,
                        self._resample_buf,
                        src_frames_chunk,
                        dst_n,
                        src_step_q16,
                        acc_local,
                    )
                    acc_local += dst_n * src_step_q16
                    acc_local -= chunk_end_q16
                    self._write_all(self._resample_mv[:dst_n * 2])
                else:
                    self._write_all(self._wav_out_mv[:out_n])

        self._drain_tail(tail_margin_ms=8)

        if self._rate != default_rate:
            self._ensure_tx_mode(rate=default_rate)

    def _ensure_resample_buf(self, src_rate, dst_rate):
        ratio = max(1.0, float(dst_rate) / float(src_rate))
        needed = int(self._WAV_BUFFER_FRAMES * ratio + 8) * 2
        if self._resample_buf is None or len(self._resample_buf) < needed:
            self._resample_buf = bytearray(needed)
            self._resample_mv = memoryview(self._resample_buf)

    def _write_all(self, mv):
        view = mv if isinstance(mv, memoryview) else memoryview(mv)
        off = 0
        n = len(view)
        stall_us = 50
        write = self._i2s.write
        while off < n:
            w = write(view[off:])
            if not w:
                time.sleep_us(stall_us)
                if stall_us < 1000:
                    stall_us <<= 1
                continue
            stall_us = 50
            off += w

    def _rest_ms(self, ms):
        ms = int(ms)
        if ms <= 0:
            return

        total_bytes = int(self._rate * ms / 1000.0 + 0.5) * 2
        if total_bytes <= 0:
            return

        left = total_bytes
        z_mv = self._silence_buf
        z_len = len(z_mv)
        while left > 0:
            take = z_len if left > z_len else left
            self._write_all(z_mv[:take])
            left -= take

    def _drain_tail(self, tail_margin_ms=None):
        if self._mode != self._MODE_TX or self._i2s is None:
            return

        margin = self._TAIL_MARGIN_MS if tail_margin_ms is None else int(tail_margin_ms)
        tail_ms = (self._ibuf * 1000) // (2 * self._rate) + margin
        self._rest_ms(tail_ms)

    def _play_sine(self, freq_hz, duration_ms, fade_ms):
        if freq_hz <= 0.0 or duration_ms <= 0:
            self._rest_ms(duration_ms)
            return

        amp_q15 = self._vol_to_q15(self._vol)
        total_samples = int(self._rate * duration_ms / 1000.0 + 0.5)
        fade_samples = max(1, int(self._rate * fade_ms / 1000.0 + 0.5))
        if fade_samples * 2 > total_samples:
            fade_samples = max(1, total_samples // 2)

        sine_bits = self._SINE_BITS
        frac_bits = self._SINE_FRAC_BITS
        shift = 32 - sine_bits
        idx_mask = (1 << sine_bits) - 1
        frac_mask = (1 << frac_bits) - 1
        sine_bias = self._SINE_BIAS
        fade_n = self._FADE_TABLE_SIZE

        phase = 0
        step = int((freq_hz * (1 << 32)) / self._rate)

        sent = 0
        while sent < total_samples:
            todo = min(self._TONE_CHUNK_FRAMES, total_samples - sent)
            phase = self._render_sine_chunk(
                todo,
                sent,
                total_samples,
                fade_samples,
                amp_q15,
                phase,
                step,
                shift,
                self._sine_table,
                self._tone_buf,
                self._fade_curve,
                fade_n,
                sine_bias,
                frac_bits,
                frac_mask,
                idx_mask,
            )
            self._write_all(self._tone_mv[:todo * 2])
            sent += todo

    @micropython.viper
    def _apply_vol_pcm16(self, buf, n_bytes: int, vol_q15: int, dither: int, noise, dither_idx: int, mask: int) -> int:
        buf_ptr = ptr8(addressof(buf))
        n_samples: int = n_bytes >> 1
        off: int = 0
        di: int = dither_idx
        s16: int = 0
        d: int = 0
        if dither != 0:
            noise_ptr = ptr8(addressof(noise))
            for k in range(n_samples):
                s16 = int(buf_ptr[off]) | (int(buf_ptr[off + 1]) << 8)
                if s16 >= 32768:
                    s16 -= 65536
                d = int(noise_ptr[di]) - 1
                di = (di + 1) & mask
                s16 = (s16 * vol_q15 + (16384 + (d << 14))) >> 15
                if s16 > 32767:
                    s16 = 32767
                elif s16 < -32768:
                    s16 = -32768
                buf_ptr[off] = s16 & 0xFF
                buf_ptr[off + 1] = (s16 >> 8) & 0xFF
                off += 2
        else:
            for k in range(n_samples):
                s16 = int(buf_ptr[off]) | (int(buf_ptr[off + 1]) << 8)
                if s16 >= 32768:
                    s16 -= 65536
                s16 = (s16 * vol_q15 + 16384) >> 15
                buf_ptr[off] = s16 & 0xFF
                buf_ptr[off + 1] = (s16 >> 8) & 0xFF
                off += 2
        return di

    @micropython.viper
    def _resample_nn_16(self, src, dst, src_n: int, dst_n: int, src_step_q16: int, acc_in: int) -> int:
        src_ptr = ptr8(addressof(src))
        dst_ptr = ptr8(addressof(dst))
        acc: int = acc_in
        max_idx: int = src_n - 1
        if max_idx < 0:
            max_idx = 0
        out_off: int = 0
        si: int = 0
        s_off: int = 0
        for j in range(dst_n):
            si = acc >> 16
            if si > max_idx:
                si = max_idx
            s_off = si << 1
            dst_ptr[out_off] = src_ptr[s_off]
            dst_ptr[out_off + 1] = src_ptr[s_off + 1]
            out_off += 2
            acc += src_step_q16
        return acc

    @micropython.viper
    def _convert_wav_8mono(self, src, dst, n_frames: int, vol_q15: int) -> int:
        src_ptr = ptr8(addressof(src))
        dst_ptr = ptr8(addressof(dst))
        off: int = 0
        for k in range(n_frames):
            b: int = int(src_ptr[k])
            s16: int = (b - 128) << 8
            s16 = (s16 * vol_q15) >> 15
            dst_ptr[off] = s16 & 0xFF
            dst_ptr[off + 1] = (s16 >> 8) & 0xFF
            off += 2
        return off

    @micropython.viper
    def _convert_wav_8stereo(self, src, dst, n_frames: int, vol_q15: int) -> int:
        src_ptr = ptr8(addressof(src))
        dst_ptr = ptr8(addressof(dst))
        off: int = 0
        for k in range(n_frames):
            i: int = k * 2
            left: int = (int(src_ptr[i]) - 128) << 8
            right: int = (int(src_ptr[i + 1]) - 128) << 8
            s16: int = (left + right) >> 1
            s16 = (s16 * vol_q15) >> 15
            dst_ptr[off] = s16 & 0xFF
            dst_ptr[off + 1] = (s16 >> 8) & 0xFF
            off += 2
        return off

    @micropython.viper
    def _convert_wav_16mono(self, src, dst, n_frames: int, vol_q15: int) -> int:
        src_ptr = ptr8(addressof(src))
        dst_ptr = ptr8(addressof(dst))
        off: int = 0
        for k in range(n_frames):
            i: int = k * 2
            s16: int = int(src_ptr[i]) | (int(src_ptr[i + 1]) << 8)
            if s16 >= 32768:
                s16 -= 65536
            s16 = (s16 * vol_q15) >> 15
            dst_ptr[off] = s16 & 0xFF
            dst_ptr[off + 1] = (s16 >> 8) & 0xFF
            off += 2
        return off

    @micropython.viper
    def _convert_wav_16stereo(self, src, dst, n_frames: int, vol_q15: int) -> int:
        src_ptr = ptr8(addressof(src))
        dst_ptr = ptr8(addressof(dst))
        off: int = 0
        for k in range(n_frames):
            i: int = k * 4
            left: int = int(src_ptr[i]) | (int(src_ptr[i + 1]) << 8)
            if left >= 32768:
                left -= 65536
            right: int = int(src_ptr[i + 2]) | (int(src_ptr[i + 3]) << 8)
            if right >= 32768:
                right -= 65536
            s16: int = (left + right) >> 1
            s16 = (s16 * vol_q15) >> 15
            dst_ptr[off] = s16 & 0xFF
            dst_ptr[off + 1] = (s16 >> 8) & 0xFF
            off += 2
        return off

    @micropython.viper
    def _render_sine_chunk(
        self,
        todo: int,
        sent: int,
        total_samples: int,
        fade_samples: int,
        amp_q15: int,
        phase: int,
        step: int,
        shift: int,
        tbl,
        buf,
        fade_curve,
        fade_n: int,
        sine_bias: int,
        frac_bits: int,
        frac_mask: int,
        idx_mask: int,
    ) -> int:
        buf_ptr = ptr8(addressof(buf))
        tbl_ptr = ptr16(addressof(tbl))
        fade_ptr = ptr16(addressof(fade_curve))
        off: int = 0
        for i in range(todo):
            phase = phase + step
            idx: int = (phase >> shift) & idx_mask
            frac: int = (phase >> (shift - frac_bits)) & frac_mask

            v1: int = int(tbl_ptr[idx]) - sine_bias
            v2: int = int(tbl_ptr[(idx + 1) & idx_mask]) - sine_bias
            base: int = v1 + (((v2 - v1) * frac) >> frac_bits)

            s16: int = (base * amp_q15 + 16384) >> 15

            p: int = sent + i
            if p < fade_samples:
                fi: int = (p * fade_n) // fade_samples
                if fi >= fade_n:
                    fi = fade_n - 1
                g: int = int(fade_ptr[fi])
                s16 = (s16 * g + 16384) >> 15
            else:
                rem: int = total_samples - p
                if rem <= fade_samples:
                    fi2: int = (rem * fade_n) // fade_samples
                    if fi2 >= fade_n:
                        fi2 = fade_n - 1
                    g2: int = int(fade_ptr[fi2])
                    s16 = (s16 * g2 + 16384) >> 15

            buf_ptr[off] = s16 & 0xFF
            buf_ptr[off + 1] = (s16 >> 8) & 0xFF
            off += 2

        return phase

    def _note_duration_ms(self, denom):
        denom = int(denom)
        if denom == 0:
            raise ValueError('Note length cannot be zero')

        quarter_ms = 60000.0 / self._tempo
        d = abs(denom)
        base = quarter_ms * (4.0 / d)
        if denom < 0:
            base *= 1.5
        return int(base + 0.5)

    def _prep_rx_buffer(self, buffer, num_frames):
        if buffer is None:
            self._ensure_stream_bufs()
            if num_frames is None:
                n = self._stream_frames
            else:
                n = max(0, int(num_frames))
            if n > self._stream_frames:
                raise ValueError('num_frames exceeds default buffer; supply your own buffer')
            return self._stream_mv, n
        mv = buffer if isinstance(buffer, memoryview) else memoryview(buffer)
        if num_frames is None:
            n = len(mv) // 4
        else:
            n = max(0, int(num_frames))
        if len(mv) < n * 4:
            raise ValueError('Buffer is smaller than requested frame count')
        return mv, n

    def _read_raw_into(self, mv, num_frames):
        self._ensure_rx_mode()
        bytes_to_read = num_frames * 4
        if bytes_to_read <= 0:
            return 0

        target = mv[:bytes_to_read]
        bytes_read = 0
        stall_us = 50
        readinto = self._i2s.readinto
        while bytes_read < bytes_to_read:
            n = readinto(target[bytes_read:])
            if n:
                bytes_read += n
                stall_us = 50
            else:
                time.sleep_us(stall_us)
                if stall_us < 1000:
                    stall_us <<= 1

        return bytes_read

    def read_raw(self, buffer=None, num_frames=None):
        mv, n = self._prep_rx_buffer(buffer, num_frames)
        return self._read_raw_into(mv, n)

    @micropython.viper
    def _convert_32to16_gain(self, src, dst, n_frames: int, gain_q8: int) -> int:
        src_ptr = ptr32(addressof(src))
        dst_ptr = ptr8(addressof(dst))
        out_off: int = 0
        s32: int = 0
        s16: int = 0
        v: int = 0
        for i in range(n_frames):
            s32 = int(src_ptr[i])
            s16 = (s32 >> 16) & 0xFFFF
            if s16 >= 32768:
                s16 -= 65536
            v = (s16 * gain_q8) >> 8
            if v > 32767:
                v = 32767
            elif v < -32768:
                v = -32768
            dst_ptr[out_off] = v & 0xFF
            dst_ptr[out_off + 1] = (v >> 8) & 0xFF
            out_off += 2
        return out_off

    def _convert_32to16(self, src, dst, n_frames):
        return self._convert_32to16_gain(src, dst, n_frames, self._mic_gain_q8)

    @micropython.viper
    def _block_sum_int16(self, buf, off: int, n: int) -> int:
        # Pre-adjust pointer to element 'off' so the inner loop uses a plain
        # counter p[k] (k = 0..n-1).  Viper compiles simple indexed ptr16
        # accesses to efficient assembly; complex expressions like p[off+k]
        # fall back to slow Python object arithmetic.
        p = ptr16(int(addressof(buf)) + (off << 1))
        s: int = 0
        v: int = 0
        for k in range(n):
            v = int(p[k])
            if v >= 32768:
                v -= 65536
            s += v
        return s

    @micropython.viper
    def _block_sum_sq_dev(self, buf, off: int, n: int, mean_i: int, shift: int) -> int:
        # Same pre-adjustment: shift base pointer by 'off' elements so the
        # loop only ever uses p[k] with k starting at 0.
        p = ptr16(int(addressof(buf)) + (off << 1))
        s: int = 0
        v: int = 0
        d: int = 0
        for k in range(n):
            v = int(p[k])
            if v >= 32768:
                v -= 65536
            d = (v - mean_i) >> shift
            s += d * d
        return s

    @micropython.viper
    def _sum_sq_i2s32_shift(self, buf, frame_off: int, n_frames: int, shift: int) -> int:
        # Pre-adjust ptr32 to frame 'frame_off' (4 bytes per 32-bit frame).
        # Loop then uses p[i] with i from 0, enabling efficient assembly.
        # Arithmetic right-shift propagates the sign bit, eliminating the
        # manual two's-complement fixup that ptr16 required.
        p = ptr32(int(addressof(buf)) + (frame_off << 2))
        s: int = 0
        v: int = 0
        total_shift: int = 16 + shift
        for i in range(n_frames):
            v = int(p[i]) >> total_shift
            s += v * v
        return s

    def _capture_pcm16_into(self, output_mv, total_frames):
        self._ensure_rx_mode()
        self._ensure_rec_bufs()
        rec_buf = self._rec_buf
        rec_mv = self._rec_mv
        convert_buf = self._convert_buf
        convert_mv = self._convert_mv
        rec_chunk = self._REC_BUFFER_FRAMES

        frames_done = 0
        out_off = 0
        while frames_done < total_frames:
            sub = total_frames - frames_done
            if sub > rec_chunk:
                sub = rec_chunk
            br = self._read_raw_into(rec_mv, sub)
            af = br >> 2
            if af <= 0:
                continue
            bc = self._convert_32to16(rec_buf, convert_buf, af)
            output_mv[out_off:out_off + bc] = convert_mv[:bc]
            out_off += bc
            frames_done += af
        return out_off

    def read_samples(self, duration_ms):
        total_frames = int(self._rate * int(duration_ms) / 1000.0 + 0.5)
        required_bytes = total_frames * 2
        gc.collect()
        self._ensure_rec_bufs()
        # _ensure_rec_bufs() has already allocated _rec_buf and _convert_buf;
        # gc.mem_free() no longer counts those bytes.  Only compare the new
        # output buffer size against free RAM, with a 16 KB safety margin.
        if required_bytes + 16384 > gc.mem_free():
            raise MemoryError('Requested capture is too large for in-memory recording; use record_to_file() for long recordings')

        try:
            output = bytearray(required_bytes)
        except MemoryError:
            raise MemoryError('Could not allocate a contiguous recording buffer; use record_to_file() for long recordings')

        self._capture_pcm16_into(memoryview(output), total_frames)
        return output

    @staticmethod
    def _write_wav_header(f, sample_rate, data_size, num_channels=1, bits_per_sample=16):
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        # Build the entire 44-byte RIFF/WAVE header in one bytearray and
        # write it with a single f.write() call to minimise heap churn and
        # avoid partial-write inconsistency on slow storage.
        hdr = bytearray(44)
        struct.pack_into(
            '<4sI4s4sIHHIIHH4sI',
            hdr, 0,
            b'RIFF', 36 + data_size,
            b'WAVE',
            b'fmt ', 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample,
            b'data', data_size,
        )
        f.write(hdr)

    def record_to_file(self, filename, duration_ms):
        total_frames = int(self._rate * int(duration_ms) / 1000.0 + 0.5)
        data_size = total_frames * 2

        gc.collect()
        self._ensure_rec_bufs()  
        # Same reasoning as read_samples: only compare the new RAM buffer
        # against free memory, with a 16 KB safety margin.
        if data_size + 16384 > gc.mem_free():
            raise MemoryError(
                'Recording too large for available RAM; reduce duration_ms or rate'
            )

        try:
            ram_buf = bytearray(data_size)
        except MemoryError:
            raise MemoryError(
                'Could not allocate recording buffer; reduce duration_ms or rate'
            )
        ram_mv = memoryview(ram_buf)

        # Both capture and file-write are inside the same try/finally so that
        # the I2S hardware is released regardless of where a failure occurs
        # (e.g. SD card removal or disk-full during f.write).
        try:
            out_off = self._capture_pcm16_into(ram_mv, total_frames)
            with open(filename, 'wb') as f:
                self._write_wav_header(f, self._rate, out_off)
                written = 0
                chunk = self._REC_FILE_CHUNK_BYTES
                while written < out_off:
                    take = chunk if (out_off - written) > chunk else (out_off - written)
                    f.write(ram_mv[written:written + take])
                    written += take
        finally:
            if self._i2s is not None:
                self._i2s.deinit()
                self._i2s = None
            self._mode = None
            self._idle_i2s_pins()

    def get_level(self):
        self._ensure_rx_mode()
        self._ensure_stream_bufs()

        bytes_read = self.read_raw(self._stream_mv, self._stream_frames)
        n_frames = bytes_read // 4
        if n_frames <= 0:
            return self._level_state

        self._convert_32to16(self._stream_buf, self._convert_buf, n_frames)

        chunk = self._LEVEL_RMS_CHUNK
        total_sum = 0
        rem = n_frames
        off = 0
        while rem > 0:
            take = chunk if rem > chunk else rem
            total_sum += self._block_sum_int16(self._convert_buf, off, take)
            off += take
            rem -= take

        mean_i = total_sum // n_frames

        total_sq = 0
        rem = n_frames
        off = 0
        shift = 5
        while rem > 0:
            take = chunk if rem > chunk else rem
            total_sq += self._block_sum_sq_dev(self._convert_buf, off, take, mean_i, shift)
            off += take
            rem -= take

        var_int16 = (total_sq << self._LEVEL_VAR_SHIFT) / n_frames  
        rms_int16 = math.sqrt(var_int16) if var_int16 > 0.0 else 0.0

        if rms_int16 <= 0.0:
            level = 0.0
        else:
            db = 20.0 * math.log10(rms_int16 / 32768.0)
            if db <= self._LEVEL_FLOOR_DB:
                level = 0.0
            elif db >= 0.0:
                level = 1.0
            else:
                level = (db - self._LEVEL_FLOOR_DB) / (-self._LEVEL_FLOOR_DB)

        now = time.ticks_ms()
        elapsed_ms = time.ticks_diff(now, self._level_last_ms)
        self._level_last_ms = now

        if level >= self._level_state:
            self._level_state = level
        else:
            if elapsed_ms <= 0:
                elapsed_ms = self._LEVEL_WINDOW_MS
            blend = elapsed_ms / self._LEVEL_RELEASE_MS  
            if blend >= 1.0:
                self._level_state = level
            else:
                self._level_state = level + (self._level_state - level) * (1.0 - blend)

        return self._level_state

    def is_sound_detected(self, threshold=0.01):
        return self.get_level() >= float(threshold)

    def rms(self, num_frames=None, buffer=None):
        mv, n = self._prep_rx_buffer(buffer, num_frames)
        if n <= 0:
            return 0
        self._read_raw_into(mv, n)

        SHIFT = 3
        CHUNK = 128
        sum_total = 0
        off = 0
        rem = n
        while rem > 0:
            take = CHUNK if rem > CHUNK else rem
            sum_total += self._sum_sq_i2s32_shift(mv, off, take, SHIFT)
            off += take
            rem -= take

        SHIFT_SQ = SHIFT << 1  # = 6; precomputed once, no need for type annotation
        mean_sq = (sum_total << SHIFT_SQ) / n
        return int(math.sqrt(mean_sq)) if mean_sq > 0.0 else 0
