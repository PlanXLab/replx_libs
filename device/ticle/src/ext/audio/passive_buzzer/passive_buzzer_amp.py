__version__ = "1.0.0"
__author__ = "PlanX Lab Development Team"

import utime
import machine
import uasyncio as asyncio

class PassiveBuzzerAmplified:
    """
    다중 GPIO 핀을 병렬로 사용하여 전류 증폭
    주의: 동일한 타이밍으로 여러 핀을 제어해야 함
    """
    NOTE_FREQ = {
        'C':  0, 'CS': 1, 'D': 2, 'DS': 3, 'E': 4, 'F': 5,
        'FS': 6, 'G': 7, 'GS': 8, 'A': 9, 'AS': 10, 'B': 11
    }

    BASE_FREQ = 16.35

    def __init__(self, pins: list = [13, 14, 15], tempo: int = 120):
        """
        Args:
            pins: 병렬로 연결할 GPIO 핀 번호 리스트 (2-3개 권장)
        """
        self._pwm_list = []
        for pin in pins:
            pwm = machine.PWM(machine.Pin(pin))
            pwm.duty_u16(0)
            self._pwm_list.append(pwm)
        
        self._tempo = tempo
        self._max_duty = 58982  # 90%
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

    def tone(self, note_octave: str, length: int = 4):
        duration = (60 / self._tempo) * (4 / length)

        if note_octave.upper() in ['R', 'REST']:
            for pwm in self._pwm_list:
                pwm.duty_u16(0)
            utime.sleep(duration)
            return

        freq = self._note_to_freq(note_octave)
        
        # 모든 PWM 동시 설정
        for pwm in self._pwm_list:
            pwm.duty_u16(self._max_duty)
            pwm.freq(int(freq))

        utime.sleep(duration * 0.9)
        
        for pwm in self._pwm_list:
            pwm.duty_u16(0)
        utime.sleep(duration * 0.1)

    def play(self, melody):
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
            for pwm in self._pwm_list:
                pwm.duty_u16(0)
        return True

    def stop(self):
        self._is_playing = False
        for pwm in self._pwm_list:
            pwm.duty_u16(0)

    def deinit(self):
        self.stop()
        for pwm in self._pwm_list:
            pwm.deinit()
