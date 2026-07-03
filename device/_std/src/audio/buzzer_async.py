# @package: buzzer_async
# @version: 1.0.0
# @type: device-std
# @category: audio
# @interface: PWM
# @depends: buzzer
# @platforms: *
# @tags: buzzer, audio, tone, melody, rtttl, beep, music, async, asyncio
# @author: PlanXLab Development Team

import asyncio
from .buzzer import Buzzer


class BuzzerAsync:
    def __init__(self, buzzer: Buzzer):
        self._bz = buzzer

    @property
    def buzzer(self) -> Buzzer:
        return self._bz

    @property
    def tempo(self) -> int:
        return self._bz.tempo

    @tempo.setter
    def tempo(self, bpm: int):
        self._bz.tempo = bpm

    @property
    def volume(self) -> int:
        return self._bz.volume

    @volume.setter
    def volume(self, value: int):
        self._bz.volume = value

    @property
    def is_playing(self) -> bool:
        return self._bz.is_playing

    async def beep(self, freq: int = 1000, ms: int = 100):
        if freq <= 0:
            self._bz._pout.set_duty(0)
            await asyncio.sleep_ms(ms)
            return

        self._bz._pout.set_freq(freq)
        self._bz._pout.set_duty(self._bz._volume)
        await asyncio.sleep_ms(ms)
        self._bz._pout.set_duty(0)

    async def tone(self, note: str, length: int = 4, *, staccato: float = 0.9):
        freq = self._bz._note_to_freq(note)
        duration_ms = self._bz._calc_duration_ms(length)
        sound_ms = int(duration_ms * staccato)
        gap_ms = duration_ms - sound_ms

        if freq > 0:
            self._bz._pout.set_freq(freq)
            self._bz._pout.set_duty(self._bz._volume)
            await asyncio.sleep_ms(sound_ms)
            self._bz._pout.set_duty(0)
        else:
            await asyncio.sleep_ms(sound_ms)

        if gap_ms > 0:
            await asyncio.sleep_ms(gap_ms)

    async def play(self, melody, *, staccato: float = 0.9):
        if isinstance(melody, str):
            melody = Buzzer.parse_rtttl(melody)

        self._bz._is_playing = True
        try:
            for i in range(0, len(melody), 2):
                if not self._bz._is_playing:
                    break
                note = melody[i]
                length = melody[i + 1]
                await self.tone(note, length, staccato=staccato)
        finally:
            self._bz._is_playing = False
            self._bz._pout.set_duty(0)

    def stop(self):
        self._bz.stop()

    def silence(self):
        self._bz.silence()
