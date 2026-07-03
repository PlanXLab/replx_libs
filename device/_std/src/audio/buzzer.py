# @package: buzzer
# @version: 2.2.0
# @type: device-std
# @category: audio
# @interface: PWM
# @depends: pout
# @platforms: *
# @tags: buzzer, audio, tone, melody, rtttl, beep, music
# @author: PlanXLab Development Team

import time
from micropython import const

from pout import Pout

_NOTE_MAP = {
    'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
    'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11,
    'P': -1
}

_BASE_FREQ = const(16)


class Buzzer:
    MELODY_STARTUP = ('C5', 8, 'E5', 8, 'G5', 4)
    MELODY_SUCCESS = ('G4', 8, 'C5', 4)
    MELODY_ERROR = ('G3', 8, 'R', 16, 'G3', 8)
    MELODY_ALERT = ('A5', 8, 'R', 8, 'A5', 8, 'R', 8, 'A5', 8)

    def __init__(self, pin: int, *, tempo: int = 120, volume: int = 50):
        self._pout = Pout([pin])
        self._tempo = max(20, min(300, tempo))
        self._volume = max(0, min(100, volume))
        self._is_playing = False

        self._pout.set_duty(0)

    def _note_to_freq(self, note: str) -> int:
        note = note.upper().strip()
        if note in ('R', 'REST', 'P'):
            return 0

        if note[-1].isdigit():
            octave = int(note[-1])
            name = note[:-1]
        else:
            octave = 4
            name = note

        if name not in _NOTE_MAP:
            raise ValueError(f"Unknown note: {note}")

        semitone = _NOTE_MAP[name]
        if semitone < 0:
            return 0

        n = (octave * 12) + semitone
        return int(_BASE_FREQ * (2 ** (n / 12.0)) + 0.5)

    def _calc_duration_ms(self, length: int) -> int:
        beat_ms = 60000 // self._tempo
        return (beat_ms * 4) // length

    def beep(self, freq: int = 1000, ms: int = 100):
        if freq <= 0:
            self._pout.set_duty(0)
            time.sleep_ms(ms)
            return

        self._pout.set_freq(freq)
        self._pout.set_duty(self._volume)
        time.sleep_ms(ms)
        self._pout.set_duty(0)

    def tone(self, note: str, length: int = 4, *, staccato: float = 0.9):
        freq = self._note_to_freq(note)
        duration_ms = self._calc_duration_ms(length)
        sound_ms = int(duration_ms * staccato)
        gap_ms = duration_ms - sound_ms

        if freq > 0:
            self._pout.set_freq(freq)
            self._pout.set_duty(self._volume)
            time.sleep_ms(sound_ms)
            self._pout.set_duty(0)
        else:
            time.sleep_ms(sound_ms)

        if gap_ms > 0:
            time.sleep_ms(gap_ms)

    def silence(self):
        self._pout.set_duty(0)

    def play(self, melody):
        if isinstance(melody, str):
            melody = self.parse_rtttl(melody)

        if self._is_playing:
            return False

        self._is_playing = True
        try:
            for i in range(0, len(melody), 2):
                if not self._is_playing:
                    break
                note = melody[i]
                length = melody[i + 1]
                self.tone(note, length)
        finally:
            self._is_playing = False
            self._pout.set_duty(0)
        return True

    @staticmethod
    def parse_rtttl(rtttl: str) -> tuple:
        parts = rtttl.strip().split(':')
        if len(parts) != 3:
            raise ValueError("Invalid RTTTL format")

        defaults = parts[1].lower()
        notes_str = parts[2]

        d_duration = 4
        d_octave = 6
        d_bpm = 63

        for param in defaults.split(','):
            param = param.strip()
            if param.startswith('d='):
                d_duration = int(param[2:])
            elif param.startswith('o='):
                d_octave = int(param[2:])
            elif param.startswith('b='):
                d_bpm = int(param[2:])

        melody = []
        for note_str in notes_str.split(','):
            note_str = note_str.strip().lower()
            if not note_str:
                continue

            duration = d_duration
            octave = d_octave
            dotted = False

            idx = 0
            dur_str = ''
            while idx < len(note_str) and note_str[idx].isdigit():
                dur_str += note_str[idx]
                idx += 1
            if dur_str:
                duration = int(dur_str)

            note_name = ''
            if idx < len(note_str):
                note_name = note_str[idx].upper()
                idx += 1

            if idx < len(note_str) and note_str[idx] == '#':
                note_name += '#'
                idx += 1

            if idx < len(note_str) and note_str[idx] == '.':
                dotted = True
                idx += 1

            oct_str = ''
            while idx < len(note_str) and note_str[idx].isdigit():
                oct_str += note_str[idx]
                idx += 1
            if oct_str:
                octave = int(oct_str)

            if idx < len(note_str) and note_str[idx] == '.':
                dotted = True

            if note_name == 'P':
                melody.append('R')
            else:
                melody.append(f"{note_name}{octave}")

            if dotted:
                melody.append(int(duration * 2 / 3))
            else:
                melody.append(duration)

        return tuple(melody)

    def stop(self):
        self._is_playing = False
        self._pout.set_duty(0)

    @property
    def tempo(self) -> int:
        return self._tempo

    @tempo.setter
    def tempo(self, bpm: int):
        if bpm < 20 or bpm > 300:
            raise ValueError("Tempo must be 20-300 BPM")
        self._tempo = bpm

    @property
    def volume(self) -> int:
        return self._volume

    @volume.setter
    def volume(self, value: int):
        if value < 0 or value > 100:
            raise ValueError("Volume must be 0-100")
        self._volume = value

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def deinit(self):
        self.stop()
        self._pout.deinit()
