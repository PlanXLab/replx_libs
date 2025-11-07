__version__ = "1.0.0"
__author__ = "PlanX Lab Development Team"

import utime
import machine
import uasyncio as asyncio

class PassiveBuzzer:
    NOTE_FREQ = {
        'C':  0, 'CS': 1, 'D': 2, 'DS': 3, 'E': 4, 'F': 5,
        'FS': 6, 'G': 7, 'GS': 8, 'A': 9, 'AS': 10, 'B': 11
    }

    BASE_FREQ = 16.35

    def __init__(self, pin: int = 1, tempo: int = 120, volume: int = 50, boost: bool = False):
        self._pin = machine.Pin(pin, machine.Pin.OUT)
        self._pwm = machine.PWM(self._pin)
        self._pwm.duty_u16(0)
        self._tempo = tempo
        self._volume = max(0, min(100, volume))
        self._boost = boost
        
        # Boost mode: duty cycle을 비대칭으로 설정 (소리 증폭)
        if self._boost:
            # 90% duty cycle (거의 최대)
            self._max_duty = 58982  # 약 90%
        else:
            self._max_duty = int(65535 * self._volume / 100)
        
        self._is_playing = False
        self._melody_task = None

    def _note_to_freq(self, note_octave: str) -> float:
        try:
            note = note_octave[:-1].upper()
            octave = int(note_octave[-1])
        except (IndexError, ValueError):
            raise ValueError(f"Invalid note format: {note_octave}")
        
        if note not in self.NOTE_FREQ:
            raise ValueError(f"Unknown note: {note}")
        
        n = (octave * 12) + self.NOTE_FREQ[note]
        return self.BASE_FREQ * (2 ** (n / 12))

    def tone(self, note_octave: str, length: int = 4, echo: bool = False):
        duration = (60 / self._tempo) * (4 / length)

        if note_octave.upper() in ['R', 'REST']:
            self._pwm.duty_u16(0)
            utime.sleep(duration)
            return

        freq = self._note_to_freq(note_octave)
        
        # 주파수 설정 전에 duty를 먼저 설정
        self._pwm.duty_u16(self._max_duty)
        self._pwm.freq(int(freq))

        if echo:
            echo_delay = duration * 0.1
            echo_decay = 0.5
            num_echoes = 2

            utime.sleep(duration * 0.5)
            self._pwm.duty_u16(0)
            utime.sleep(duration * 0.1)

            for i in range(num_echoes):
                utime.sleep(echo_delay)
                self._pwm.duty_u16(int(self._max_duty * (echo_decay ** (i + 1))))
                utime.sleep(duration * 0.2)
                self._pwm.duty_u16(0)
                utime.sleep(duration * 0.1)
        else:
            utime.sleep(duration * 0.9)
            self._pwm.duty_u16(0)
            utime.sleep(duration * 0.1)

    async def _tone_async(self, note_octave: str, length: int = 4, echo: bool = False):
        duration = (60 / self._tempo) * (4 / length)

        if note_octave.upper() in ['R', 'REST']:
            self._pwm.duty_u16(0)
            await asyncio.sleep(duration)
            return

        freq = self._note_to_freq(note_octave)
        
        # 주파수 설정 전에 duty를 먼저 설정
        self._pwm.duty_u16(self._max_duty)
        self._pwm.freq(int(freq))

        if echo:
            echo_delay = duration * 0.1
            echo_decay = 0.5
            num_echoes = 2

            await asyncio.sleep(duration * 0.5)
            self._pwm.duty_u16(0)
            await asyncio.sleep(duration * 0.1)

            for i in range(num_echoes):
                if not self._is_playing:
                    break
                await asyncio.sleep(echo_delay)
                self._pwm.duty_u16(int(self._max_duty * (echo_decay ** (i + 1))))
                await asyncio.sleep(duration * 0.2)
                self._pwm.duty_u16(0)
                await asyncio.sleep(duration * 0.1)
        else:
            await asyncio.sleep(duration * 0.9)
            self._pwm.duty_u16(0)
            await asyncio.sleep(duration * 0.1)

    async def _play_async(self, melody, echo: bool = False):
        self._is_playing = True
        try:
            for i in range(0, len(melody), 2):
                if not self._is_playing:
                    break
                note = melody[i]
                length = melody[i + 1]
                await self._tone_async(note, length, echo)
        finally:
            self._is_playing = False
            self._pwm.duty_u16(0)

    def play(self, melody, background: bool = False, echo: bool = False):
        if self._is_playing:
            return False
        
        if background:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
            
            self._melody_task = loop.create_task(self._play_async(melody, echo))
            return True
        else:
            self._is_playing = True
            try:
                for i in range(0, len(melody), 2):
                    if not self._is_playing:
                        break
                    note = melody[i]
                    length = melody[i + 1]
                    self.tone(note, length, echo)
            finally:
                self._is_playing = False
                self._pwm.duty_u16(0)
            return True

    def stop(self):
        self._is_playing = False
        self._pwm.duty_u16(0)
        if self._melody_task:
            try:
                self._melody_task.cancel()
            except:
                pass
            self._melody_task = None

    def set_tempo(self, bpm: int):
        if bpm <= 0:
            raise ValueError("BPM must be positive")
        self._tempo = bpm

    def set_volume(self, volume: int):
        if volume < 0 or volume > 100:
            raise ValueError("Volume must be between 0 and 100")
        self._volume = volume
        if not self._boost:
            self._max_duty = int(65535 * self._volume / 100)

    def set_boost(self, enabled: bool):
        self._boost = enabled
        if self._boost:
            self._max_duty = 58982  # 90%
        else:
            self._max_duty = int(65535 * self._volume / 100)

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def deinit(self):
        self.stop()
        self._pwm.deinit()
        self._pwm.deinit()
